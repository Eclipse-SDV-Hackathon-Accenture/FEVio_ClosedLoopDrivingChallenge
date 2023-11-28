import glob
import os
import sys
import asyncio
import ecal_carla_bridge.message_builder as mb

from ecal_carla_bridge.bridge_car import BridgeCar
from ecal_carla_bridge.transform_publisher import TransformPublisher
os.environ['PYTHONASYNCIODEBUG'] = '1'

import ros.sensor_msgs.Image_pb2 as img
import ros.sensor_msgs.PointCloud2_pb2 as pc
import ros.sensor_msgs.NavSatFix_pb2 as gnss
import ros.sensor_msgs.Imu_pb2 as imu
import ecal_carla_bridge.AckermannDrive_pb2 as drive_msg

from ecal_carla_bridge.config.bridge_configurator import BridgeConfigurator

import ecal_carla_bridge.configuration.config_schema as schema

import ecal.core.core as ecal_core
from ecal.core.publisher import ProtoPublisher
from ecal.core.subscriber import ProtoSubscriber

async def bridge(args, configurator):
    ecal_core.initialize(sys.argv, "Carla sensor publisher")
    client = carla.Client(args.ip, int(args.port))
    client.set_timeout(10.0)
    world = client.get_world()
    #settings = world.get_settings()
    #settings.fixed_delta_seconds = 0.05
    #world.apply_settings(settings)

    sim = CarlaSim(client, world, configurator)

    while True:
        sim.update_sensor_list()
        try:
            await asyncio.sleep(1)
        except asyncio.CancelledError as e:
            print(e)
            pass
    
import carla
import argparse

class CarlaSim():
    def __init__(self, client, world, configurator) -> None:
        self.client = client
        self.world = world
        self.car_list = []
        self.config = configurator
        self.registered_sensor_dict = {}
        self.transform_publisher = TransformPublisher()
        self.update_sensor_list()

    def update_sensor_list(self):
        self.register_new_sensors()
        self.unregister_deleted_sensors()

    def register_new_sensors(self) -> None:
        sim_sensor_list = self.get_all_sensors()
        for sensor in sim_sensor_list:
            if sensor.parent == None:
                continue
            if self.has_sensor(sensor):
                continue
            self.add_sensor(sensor)
            self.check_for_configuration(sensor)
            
    def check_for_configuration(self, sensor):
        car_settings = self.config.get_car_settings(sensor.parent)
        if car_settings == None:
            return
        sensor_settings = car_settings.get_sensor_setting(sensor)
        if sensor_settings == None:
            return
        if sensor_settings.publish == True:
            self.register_sensor(sensor, sensor_settings, car_settings.car_instruction_topic)
            self.transform_publisher.register_sensor(sensor)

    def unregister_deleted_sensors(self) -> None:
        sim_sensor_list = self.get_all_sensors()
        for sensor in list(self.registered_sensor_dict.values()):
            is_removed = True
            for sim_sensor in sim_sensor_list:
                if sim_sensor.id == sensor.id:
                    is_removed = False
                    break
            if is_removed:
                self.unregister_sensor(sensor)
                self.transform_publisher.unregister_sensor(sensor)
                self.remove_sensor(sensor)
                del sensor

    def add_sensor(self, sensor: carla.Sensor) -> None:
        self.registered_sensor_dict[sensor.id] = sensor

    def remove_sensor(self, sensor: carla.Sensor) -> None:
        self.registered_sensor_dict.pop(sensor.id)

    def register_sensor(self, sensor: carla.Sensor, sensor_settings, sub_topic=None) -> None:
        get_message_func, message_type = self.get_message_functions(sensor, sensor_settings)
        if get_message_func == None or message_type == None:
            return
        publisher = create_publisher(message_type, sensor_settings.topic)
        subscriber = create_subscriber(sub_topic) if sub_topic != None else None
        self.attach_sensor_to_car(sensor, publisher, get_message_func, subscriber)
        
    def attach_sensor_to_car(self, sensor, publisher, get_message_func, subscriber):
        car = self.get_car_object(sensor.parent)
        if car == None:
            car = BridgeCar(sensor, publisher, get_message_func, subscriber)
            self.car_list.append(car)
            return
        car.attach_sensor(sensor, publisher, get_message_func, subscriber)
    
    def get_message_functions(self, sensor, sensor_settings):
        if sensor_settings.convert_module != None:
            get_message_func = sensor_settings.convert_module.convert_function
            message_type = sensor_settings.convert_module.message_type
        else:
            try:
                message_type, get_message_func = get_sensor_message_type(sensor)
            except (SensorNotImplementedError, SensorNotSupportedError) as e:
                print(e)
                return None, None
        return get_message_func, message_type
            
    def unregister_sensor(self, sensor):
        car = self.get_car_object(sensor.parent)
        if car != None:
            car.unattach_sensor(sensor)
            if car.has_sensors() == False:
                self.car_list.remove(car)
                del car

    def has_sensor(self, sensor: carla.Sensor) -> bool:
        if sensor.id in self.registered_sensor_dict:
            return True
        return False
                 
    def get_car_object(self, new_car: carla.Vehicle) -> carla.Vehicle:
        for car in self.car_list:
            if car.vehicle.id == new_car.id:
                return car
        return None
    
    def get_all_vehicle(self):
        vehicles = self.world.get_actors().filter('*vehicle*')
        return vehicles

    def get_all_sensors(self):
        sensors = self.world.get_actors().filter('*sensor*')
        return sensors
    
# Functions

def get_sensor_message_type(sensor: carla.Sensor):
    dict_key = sensor.type_id.split('.')[1] + '.' + sensor.type_id.split('.')[2]
    type_function_dict = get_type_function_dict()
    try:
        type_function = type_function_dict[dict_key]
    except:
        raise SensorNotSupportedError() 
    if isinstance(type_function, SensorNotImplementedError):
        raise type_function
    return type_function
    
def get_type_function_dict() -> dict:
    type_function_dict = {}

    type_function_dict['camera.rgb'] = (img.Image, mb.rgb_image_to_message)
    type_function_dict['camera.semantic_segmentation'] = (img.Image, mb.semseg_image_to_message)
    type_function_dict['camera.depth'] = SensorNotImplementedError()
    type_function_dict['camera.optical_flow'] = SensorNotImplementedError()
    type_function_dict['camera.normals'] = SensorNotImplementedError()
    type_function_dict['camera.dvs'] = SensorNotImplementedError()
    type_function_dict['camera.instance_segmentation'] = SensorNotImplementedError()
    type_function_dict['other.collision'] = SensorNotImplementedError()
    type_function_dict['other.lane_invasion'] = SensorNotImplementedError()
    type_function_dict['other.imu'] = (imu.Imu, mb.imu_to_message)
    type_function_dict['other.gnss'] = (gnss.NavSatFix, mb.gnss_to_message)
    type_function_dict['other.obstacle'] = SensorNotImplementedError()
    type_function_dict['other.radar'] = (pc.PointCloud2, mb.radar_to_message)
    type_function_dict['other.rss'] = SensorNotImplementedError()
    type_function_dict['lidar.ray_cast'] = (pc.PointCloud2, mb.lidar_to_message)
    type_function_dict['lidar.ray_cast_semantic'] = SensorNotImplementedError()

    return type_function_dict

def create_publisher(type, topic):
    try:
        new_publisher = ProtoPublisher(topic, type)
    except Exception as e:
        print(e)
        return None
    return new_publisher

def create_subscriber(topic):
    try:
        new_subscriber = ProtoSubscriber(topic, drive_msg.AckermannDrive)
    except Exception as e:
        print(e)
        return None
    return new_subscriber

import platform        

def parse_args():
    parser = argparse.ArgumentParser(description='Process ip and port.')
    parser.add_argument("--ip", default="localhost")
    parser.add_argument("--port", default="2000")
    if str(platform.system()).lower() == 'windows':
        parser.add_argument("--compose", default="ecal_carla_bridge\config\config_compose.yml")
    if str(platform.system()).lower() == 'linux':
        parser.add_argument("--compose", default="ecal_carla_bridge/config/config_compose.yml")
    return parser.parse_args()

#Exceptions

class SensorNotImplementedError(Exception):
    def __init__(self, message='This sensor type is not supported by the carla bridge. Please consider implementing it by yourself!'):
        self.message = message

class SensorNotSupportedError(Exception):
    def __init__(self, message='This sensor was not supportet by the carla Simulation when the bridge recieved its last update. Please check for typos or add the new sensor yourself!'):
        self.message = message

def main():
    args = parse_args()
    try:
        lookup_path = os.path.join('ecal_carla_bridge', 'config', 'car_configs')
        configurator = BridgeConfigurator(args.compose, lookup_path)
    except FileNotFoundError as e:
        print(e)
        exit()
    except schema.SchemaError as e:
        print(e)
        exit()
    asyncio.run(bridge(args, configurator))
    
    
if __name__ == '__main__':
    package_dir = os.path.join(os.path.dirname(__file__), '..')
    sys.path.append(package_dir)
    main()
import os
import sys
import importlib

from ecal_carla_bridge.configuration.configurator import Configurator
from ecal_carla_bridge.configuration import compose_schema, config_schema



class LoadModuleError(Exception):
    def __init__(self) -> None:
        pass

class BridgeModule():
    def __init__(self, module_name, convert_function_name, message_type_function_name):
        self.module = None
        self.convert_function = None
        self.message_type = None
        self.load_module(module_name, convert_function_name, message_type_function_name)

    def load_module(self, module_name, convert_function_name, message_type_function_name):
        try:
            target = importlib.util.find_spec('ecal_carla_bridge.config.convert_modules')
            target_module_path = os.path.join(target.submodule_search_locations[0], module_name) + '.py'
            spec = importlib.util.spec_from_file_location(module_name, target_module_path)
            self.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.module)
            self.convert_function = getattr(self.module, convert_function_name)
            get_message_type = getattr(self.module, message_type_function_name)
            self.message_type = get_message_type()
        except Exception as e:
            print(e)
            raise LoadModuleError()
       

class CarSetting():
    def __init__(self, car_name: str, car_instruction_topic: str):
        self.car_name = car_name
        self.car_instruction_topic = car_instruction_topic
        self.sensor_settings = {}

    def add_sensor_settings(self, sensor_settings):
        self.sensor_settings[sensor_settings.config_key] = sensor_settings

    def get_sensor_setting(self, sensor):
        role_name = sensor.attributes['role_name']
        if role_name in self.sensor_settings:
            return self.sensor_settings[role_name]
        return None

class SensorSetting():
    def __init__(self, config_key: str, topic: str, publish: bool, algorithm: str, type: str, convert_module):
        self.config_key = config_key
        self.topic = topic
        self.algorithm = algorithm
        self.publish = publish
        self.type = type
        self.convert_module = convert_module

class BridgeConfigurator(Configurator):
    def __init__(self, compose_path, lookup_path):
        super().__init__(compose_path)
        self.car_settings_dict = self.create_settings(lookup_path)
    
    def create_settings(self, lookup_path):
        settings = {}
        car_config_filenames = self.compose_config['configs']['config_filenames']
        for car_config_filename in car_config_filenames:
            config_path = os.path.join(lookup_path, car_config_filename)
            config = self.load_config(config_path)
            config = {'car_config': config["car_config"]}
            config_schema.car_config.validate(config)
            car_config = config['car_config']
            car_name = car_config['car_name']
            car_instruction_topic = car_config['car_instruction_topic']
            car_setting = CarSetting(car_name, car_instruction_topic)
            for sensor_config in car_config['sensors']:
                config_key = sensor_config['config_key']
                topic = sensor_config['topic']
                publish = sensor_config['publish']
                algorithm = sensor_config['algorithm']
                sensor_type = sensor_config['type']
                try:
                    convert_module = self.get_config_convert_module(sensor_config)
                except LoadModuleError as e:
                    convert_module = None
                car_setting.add_sensor_settings(SensorSetting(config_key,
                                                              topic, 
                                                              publish, 
                                                              algorithm, 
                                                              sensor_type, 
                                                              convert_module))
            settings[car_name] = car_setting
        return settings
    
    def get_car_settings(self, vehicle) -> CarSetting:
        car_name = vehicle.attributes['role_name']
        for car_setting in self.car_settings_dict.values():
            if car_name not in car_setting.car_name:
                continue
            return car_setting
        return None
    
    def get_sensor_settings(self, sensor):
        config_key = sensor.attributes['role_name']
        for car_setting in self.car_settings_dict.values():
            if config_key in car_setting.sensor_settings:
                return car_setting.sensor_settings[config_key]
        return None
    
    def get_config_convert_module(self, sensor_config):
        if 'convert_module' in sensor_config:
            module_config = sensor_config['convert_module']
            module_name = module_config['module_name']
            convert_function_name = module_config['convert_function']
            message_type_function_name = module_config['message_type_function']
            convert_module = BridgeModule(module_name, convert_function_name, message_type_function_name)
            return convert_module
        return None
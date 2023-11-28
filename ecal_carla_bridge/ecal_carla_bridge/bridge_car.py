from ecal.core.publisher import ProtoPublisher
from ecal_carla_bridge.bridge_sensor import BridgeSensor
import carla
import math

class BridgeCar():
    def __init__(self, sensor: carla.Sensor , publisher: ProtoPublisher, get_message_func, subscriber, car_name=None) -> None:
        self.subscriber = None
        self.car_name = car_name
        self.vehicle = sensor.parent
        self.sensor_list = []
        self.frame_id = self.vehicle.type_id
        self.identifier = str(self.vehicle.id) + '.' + str(self.vehicle.type_id) + '.'
        self.attach_sensor(sensor, publisher, get_message_func, subscriber)

    def attach_sensor(self, sensor: carla.Sensor, publisher: ProtoPublisher, get_message_func, subscriber) -> None:
        if self.subscriber == None:
            self.subscriber = subscriber.set_callback(self.callback)
        self.sensor_list.append(BridgeSensor(sensor, publisher, get_message_func))

    def unattach_sensor(self, sensor: carla.Sensor) -> None:
        for car_sensor in self.sensor_list:
            if sensor == car_sensor.sensor:
                self.sensor_list.remove(car_sensor)
                car_sensor.stop_tasks()
                if len(self.sensor_list) == 0 and self.subscriber != None:
                    self.subscriber.c_subscriber.destroy()
                break

    def is_sensor_attached(self, sensor: carla.Sensor) -> bool:
        for car_sensor in self.sensor_list:
            if car_sensor.sensor.id == sensor.id:
                return True
        return False 
    
    def has_sensors(self):
        if len(self.sensor_list) == 0:
            return False
        return True
    
    def callback(self, topic_name, msg, time):
        steer = msg.steering_angle
        control = self.vehicle.get_control()
        control.steer = steer

        control.throttle = 0.28
        # Apply the control, keeping throttle and brake at their current values
        self.vehicle.apply_control(control)

        velocity = self.vehicle.get_velocity()
        speed = 3.6 * math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2)
        print('{} km/h'.format(speed))
 
        '''
        needs to be changed!
        steer = msg.steering_angle
        steer_speed = msg.steering_angle_velocity
        speed = msg.speed
        acceleration = msg.acceleration
        jerk = msg.jerk
        ackermann_control = carla.VehicleAckermannControl(steer=steer, steer_speed=steer_speed, speed=speed, acceleration=acceleration, jerk=jerk)
        self.vehicle.apply_ackermann_control(ackermann_control)
        '''
        

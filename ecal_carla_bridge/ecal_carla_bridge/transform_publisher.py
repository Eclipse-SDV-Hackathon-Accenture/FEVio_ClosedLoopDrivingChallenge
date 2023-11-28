import ecal_carla_bridge.message_builder as mb
import asyncio
from ecal.core.publisher import ProtoPublisher
import ros.tf2_msgs.TFMessage_pb2 as trans

import carla

class TransformPublisher():
    def __init__(self) -> None:
        self.sensor_list = []
        self.publisher = ProtoPublisher('transform_topic', trans.TFMessage)
        self.event_loop = asyncio.get_event_loop()
        self.send_trans_task = self.event_loop.create_task(self.send_transforms())

    def register_sensor(self, sensor: carla.Sensor) -> None:
        self.sensor_list.append(sensor)

    def unregister_sensor(self, sensor: carla.Sensor) -> None:
        for list_sensor in self.sensor_list:
            if sensor.id == list_sensor.id:
                self.sensor_list.remove(list_sensor)

    async def send_transforms(self) -> None:
        while True:
            for sensor in self.sensor_list:
                sensor_transform = self.get_sensor_transformation(sensor)
                transform_msg = mb.transformations_to_message(((sensor.parent.get_transform(), 'map', sensor.parent.type_id), (sensor_transform, sensor.parent.type_id, sensor.type_id)))
                self.publisher.send(transform_msg)
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError as e:
                print(e)

    def get_sensor_transformation(self, sensor): 
        sensor_rotation = sensor.get_transform().rotation
        parent_rotation = sensor.parent.get_transform().rotation
        yaw = sensor_rotation.yaw - parent_rotation.yaw
        roll = sensor_rotation.roll - parent_rotation.yaw
        pitch = sensor_rotation.pitch - parent_rotation.pitch
        return carla.Transform(sensor.get_transform().location - sensor.parent.get_transform().location, carla.Rotation(yaw, roll, pitch))

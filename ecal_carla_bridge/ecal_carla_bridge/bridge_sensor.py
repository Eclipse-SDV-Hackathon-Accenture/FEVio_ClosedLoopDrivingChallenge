import carla
from ecal.core.publisher import ProtoPublisher
import asyncio

class BridgeSensor():
    def __init__(self, sensor: carla.Sensor, data_publisher: ProtoPublisher, message_convert_func) -> None:
        self.sensor = sensor
        self.convert_func = message_convert_func
        self.data_queue = asyncio.Queue()
        self.event_loop = asyncio.get_event_loop()
        self.data_publisher = data_publisher
        self.frame_id = sensor.type_id
        if self.data_publisher != None:
            self.start_listen() 
            self.task = self.event_loop.create_task(self.send_messages())

    def stop_tasks(self) -> None:
        self.task.cancel()
        self.data_publisher.c_publisher.destroy()

    def start_listen(self) -> None:
        self.sensor.listen(self.data_queue.put_nowait)

    def get_next_dataset(self):
        return self.data_queue.get()
    
    def add_dataset(self, dataset):
        self.data_queue.put_nowait(dataset)
    
    async def send_messages(self):
        while True:
            try:
                data = await self.data_queue.get()
                self.data_publisher.send(self.convert_func(data, self.frame_id))
            except Exception as e:
                print(e)

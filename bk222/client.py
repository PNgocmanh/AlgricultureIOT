from task import *
from utils.logger import *
from paho.mqtt import client as mqtt_client
import random
from dotenv import load_dotenv
import os
import json
from queue import Queue

load_dotenv()


class SystemManager:
    logger = Logger('SYSTEM')

    def __init__(self):
        self.broker = os.getenv("T_BROKER")
        self.port = os.getenv("T_PORT")
        self.username = os.getenv("T_USERNAME")
        self.password = os.getenv("T_PASSWORD")
        self.queue = Queue()
        self.time_start = time.time()
        self.task_manager = TaskManager()
        self.relays = {
            'relay1': 0,
            'relay2': 0,
            'relay3': 0,
            'relay4': 0,
            'relay5': 0,
            'relay6': 0,
            'relay7': 0,
            'relay8': 0,
        }
        try:
            client_id = f'python-mqtt-{random.randint(0, 100)}'
            self.client = mqtt_client.Client(client_id)
            self.__setup()
        except Exception as e:
            SystemManager.logger.error(e)

        self.sensor = self.task_manager.create_task('sensor', self.queue)
        self.sensor.run()
        self.model = self.task_manager.create_task('model', self.queue)
        # self.model.config_text({'list': ["healthy leaf", "wilting leaf","leaf spot","unhealthy leaf", "sick leaf"]})

    def __handle_connect(self, client, userdata, flags, rc):
        if rc == 0:
            SystemManager.logger.info("Connecting successfully!")
        else:
            SystemManager.logger.warn(f"Failed to connect, return code {rc}")

    def __handle_subscribe(self, client, userdata, mid, granted_qos):
        pass

    def __handle_disconnect(self, *args):
        SystemManager.logger.warn("Disconnected")

    def __handle_publish(self, mess, topic):
        result = self.client.publish(topic, json.dumps(mess), retain=True)
        SystemManager.logger.info(f'Result publish: {result}')
        # SystemManager.logger.warn(f"Time excuting task: {time.time() - self.time_start}")
        # SystemManager.logger.warn(f"Time send message: {time.time()*1000}")

    def __handle_message(self, client, userdata, msg):
        self.time_start = time.time()
        # SystemManager.logger.warn(f"Time receive message: {time.time()*1000}")
        message_format = json.loads(msg.payload.decode())
        SystemManager.logger.info(f"Message:{message_format}")
        if msg.topic == '/bkiot/piquihac/sensor1':
            self.sensor.setup(message_format)
        elif msg.topic == '/bkiot/piquihac/plant1':
            self.model.config_text(message_format)
            self.model.run()
        else:
            task = self.task_manager.create_task(msg.topic, self.queue, self.relays)
            task.run(message_format)

    def __setup(self):
        self.client.username_pw_set(self.username, self.password)
        self.client.on_connect = self.__handle_connect
        self.client.on_disconnect = self.__handle_disconnect
        self.client.on_message = self.__handle_message
        self.client.connect(self.broker, int(self.port))
        self.client.subscribe('/bkiot/piquihac/ferValve1')
        self.client.subscribe('/bkiot/piquihac/waterValve1')
        self.client.subscribe('/bkiot/piquihac/sensor1')
        self.client.subscribe('/bkiot/piquihac/plant1')

    def run(self):
        self.client.loop_start()
        while True:
            if not self.queue.empty():
                mess = self.queue.get()
                SystemManager.logger.info(f"Message from queue: {mess}")
                self.__handle_publish(mess['payload'], mess['topic'])

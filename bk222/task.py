from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, wait
import time
from communicate.control_peripherals import *
from threading import Lock

from clip_onnx import clip_onnx
from PIL import Image
from torchvision import transforms
from numpy import *
import numpy as np
import time
import clip
import json
import cv2


class TaskManager():
    executor = ThreadPoolExecutor()
    executor_process = ProcessPoolExecutor()
    lock = Lock()

    def create_task(self, task_name, queue, relays=[]):
        if task_name == '/bkiot/piquihac/waterValve1':
            return Pump(queue, relays)
        elif task_name == '/bkiot/piquihac/ferValve1':
            return Fertilizer(queue, relays)
        elif task_name == 'sensor':
            return Sensor(queue)
        elif task_name == 'model':
            return Model(queue)

    def do(self):
        pass

    def run(self):
        pass


class Pump(TaskManager):
    def __init__(self, q, r):
        super().__init__()
        self.q = q
        self.r = r
        # self.distance_func = get_relay('readDistance')
        # self.calc_volume = lambda h: (40 - h)*17*17*3,14
        # self.volume = {
        #     'pump': self.calc_volume(self.distance_func('pump')),
        # }

# d= 34
# h = 40

    def format_message(self):
        return {
            'topic': '/bkiot/piquihac/waterValve2',
            'payload': {
                'valve4': self.r['relay4'],
                'valve5': self.r['relay5'],
                'valve6': self.r['relay6'],
                'pumpIn': self.r['relay7'],
                'pumpOut': self.r['relay8'],
                # 'vDrum': self.volume,
            }
        }

    def control_relay(self, relay, state):
        func = get_relay(relay)
        if state == 1 and self.r[relay] != state:
            func(True)
            with TaskManager.lock:
                self.r[relay] = 1
        elif state != 1 and self.r[relay] != 0:
            func(False)
            with TaskManager.lock:
                self.r[relay] = 0

    def control_pump(self, relay, state):
        func = get_relay(relay)
        func(True)
        with TaskManager.lock:
            self.r[relay] = 1
            self.q.put(self.format_message())
        while True:
            self.volume['pump'] = self.calc_volume(self.distance_func('pump'))
            if relay == 'relay7' and self.volume['pump'] >= 1000:
                func(False)
                with TaskManager.lock:
                    self.r[relay] = 0
                    self.q.put(self.format_message())
                break
            elif relay == 'relay8' and self.volume['pump'] <= 100:
                func(False)
                with TaskManager.lock:
                    self.r[relay] = 0
                    self.q.put(self.format_message())
                break
            time.sleep(0.1)

    def do(self, payload):
        self.control_relay('relay4', payload['valve4'])
        self.control_relay('relay5', payload['valve5'])
        self.control_relay('relay6', payload['valve6'])
        self.control_relay('relay7', payload['pumpIn'])
        self.control_relay('relay8', payload['pumpOut'])
        self.q.put(self.format_message())

    def run(self, payload):
        future = TaskManager.executor.submit(self.do, payload)


class Fertilizer(TaskManager):
    def __init__(self, q, r):
        super().__init__()
        self.q = q
        self.r = r
        self.distance_func = get_relay('readDistance')
        # self.max_volume = 20*27*19
        self.calc_volume = lambda h: (29 - h)*27*19
        self.volume = {
            'relay1': self.calc_volume(self.distance_func('relay1')),
            # 'relay2': self.calc_volume(self.distance_func('relay2')),
            'relay3': self.calc_volume(self.distance_func('relay3')),
        }

    def format_message(self):
        return {
            'topic': '/bkiot/piquihac/ferValve2',
            'payload': {
                'valve1': self.r['relay1'],
                'valve2': self.r['relay2'],
                'valve3': self.r['relay3'],
                'v1': int(self.volume['relay1']),
                'v2': 0,
                'v3': int(self.volume['relay3']),
            }
        }

    def control_relay(self, relay, v, state=1):
        if v == 0:
            return
        func = get_relay(relay)
        func(True)
        with TaskManager.lock:
            self.r[relay] = 1
            self.q.put(self.format_message())
        while True:
            current_v = self.calc_volume(self.distance_func(relay))
            if self.volume[relay] - current_v >= v:
                func(False)
                self.volume[relay] = current_v
                with TaskManager.lock:
                    self.r[relay] = 0
                    self.q.put(self.format_message())
                break
            # time.sleep(0.1)

    def do(self, payload):
        self.control_relay(
            'relay1', payload['vIn1'], payload['valve1'])
        # self.control_relay(
        #     'relay2', payload['vIn2'], payload['valve2'])
        self.control_relay(
            'relay3', payload['vIn3'], payload['valve3'])

    def run(self, payload):
        future = TaskManager.executor.submit(self.do, payload)


class Distance(TaskManager):
    def __init__(self, q):
        super().__init__()
        self.q = q
        self.distance_func = get_relay('readDistance')
        self.calc_volume = lambda h: (40 - h)*17*17*3, 14
        self.volume = {
            'pump': self.calc_volume(self.distance_func('pump')),
        }

    def format_message(self):
        return {
            'topic': '/bkiot/piquihac/waterValve2',
            'payload': {
                # 'valve4': self.r['relay4'],
                # 'valve5': self.r['relay5'],
                # 'valve6': self.r['relay6'],
                # 'pumpIn': self.r['relay7'],
                # 'pumpOut': self.r['relay8'],
                'vDrum': self.volume['pump'],
            }
        }

    def do(self):
        while True:
            self.volume['pump'] = self.calc_volume(self.distance_func('pump'))
            self.q.put(self.format_message())
            time.sleep(10)

    def run(self):
        future = TaskManager.executor.submit(self.do)


class Sensor(TaskManager):
    def __init__(self, q):
        super().__init__()
        self.q = q
        self.timeout = 0
        self.mode = 'manual'
        self.update = 0

    def format_message(self, data_array):
        return {
            'topic': '/bkiot/piquihac/sensor2',
            'payload': {
                'nito': data_array[0],
                'photpho': data_array[1],
                'kali': data_array[2],
                'pH': data_array[3],
                'ec': data_array[4],
                'temp': data_array[5],
                'humi': data_array[6],
            }
        }

    def do(self):
        func = get_relay('readUSB')
        while True:
            if self.mode == 'auto' and self.timeout != 0:
                data = func()
                if data != -1:
                    with TaskManager.lock:
                        self.q.put(self.format_message(data))
            elif self.mode == 'manual' and self.update == 1:
                data = func()
                if data != -1:
                    with TaskManager.lock:
                        self.q.put(self.format_message(data))
                self.update = 0
            time.sleep(5 if self.timeout == 0 else self.timeout)

    def setup(self, data):
        if data['mode'] == 'auto':
            self.timeout = int(data['time']) - 8
        elif data['mode'] == 'manual':
            self.update = data['update']
        self.mode = data['mode']

    def run(self):
        future = TaskManager.executor.submit(self.do)


class VideoCapturer(object):
    def __init__(self, url_camera):
        self.url = url_camera

    def __enter__(self):
        self.capturer = cv2.VideoCapture(self.url)
        return self.capturer

    def __exit__(self, *args):
        self.capturer.release()
        cv2.destroyAllWindows()


class Model(TaskManager):
    def __init__(self, q):
        super().__init__()
        self.q = q
        self.arr_text = []
        self.arr_value = []
        self.onnx_model = clip_onnx(None)
        self.onnx_model.load_onnx(visual_path="/home/pi/CLIP/ONNX_Model/visual.onnx",
                                  textual_path="/home/pi/CLIP/ONNX_Model/textual.onnx", logit_scale=100.0000)  # model.logit_scale.exp()
        self.image_preprocess = transforms.Compose([
            transforms.Resize(224),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))
        ])
        self.text_onnx = 0
        self.onnx_model.start_sessions(providers=["CPUExecutionProvider"])
        self.camera_url = 'rtsp://admin:123456@192.168.100.135:8554/live'

    def format_message(self, data_array):
        mess = {}
        for x in data_array:
            mess.update({x: str(data_array[x])})
        return {
            'topic': '/bkiot/piquihac/plant2',
            'payload': mess,
        }

    def config_text(self, data):
        self.arr_text = data['list'].copy()
        #self.arr_text.append('Not plants')
        self.arr_text.append('Healthy plant')
        array = []
        for x in data['list']:
            array.append(f"A photo of {x} disease on leaves or stem or root or fruit of {data['name']}")
        #array.append("A photo that has no plant or leaves")
        array.append(f"A photo of healthy leaves or stem or root or fruit of {data['name']}")
        text = clip.tokenize(array).cpu()  # [3, 77]
        self.text_onnx = text.detach().cpu().numpy().astype(np.int64)
        text_features = self.onnx_model.encode_text(self.text_onnx)

    def do(self):
        with VideoCapturer(self.camera_url) as cap:
            # for i in range(5):
                # image = self.image_preprocess(Image.open(
                #     "/home/pi/CLIP/ONNX_Model/suongmai.jpg").convert("RGB")).unsqueeze(0).cpu()  # [1, 3, 224, 224]
                _, frame = cap.read()
                color_converted = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image=Image.fromarray(color_converted)
                image = self.image_preprocess(pil_image).unsqueeze(0).cpu()
                image_onnx = image.detach().cpu().numpy().astype(np.float32)
                logits_per_image, logits_per_text = self.onnx_model(
                    image_onnx, self.text_onnx)
                probs = logits_per_image.softmax(dim=-1).detach().cpu().numpy()
                self.arr_value = probs[0].copy()

                result = {}
                for x in range(len(self.arr_text)):
                    result.update({self.arr_text[x]: round(self.arr_value[x]*100, 3)})

                sorted_value = sorted(result.items(), key=lambda x: x[1], reverse=True)
                final_result = dict(sorted_value)

                if len(final_result) > 5:
                    for i in range(len(final_result) - 5):
                        final_result.popitem()
                self.q.put(self.format_message(final_result))

    def run(self):
        # future = TaskManager.executor.submit(self.do)
        self.do()

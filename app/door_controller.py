try:
    import RPi.GPIO as GPIO
except:
    pass
import time
from scripts.ymq import YSubNode, YPubNode, YPubSubNode
import threading
from datetime import datetime
from app.api import ApiConnector
import json


class DoorActuator:
    def __init__(self, topic, actuator_polarity=0, activation_time=3, gpio=26, verbose=True):
        self.thread = threading.Thread(target=self._thread)
        self.gpio = gpio
        self.topic = topic
        self.node = YSubNode(topic)
        self.activation_time = activation_time
        self.actuator_polarity = actuator_polarity
        self.verbose = verbose
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio, GPIO.OUT)
        if self.actuator_polarity:
            GPIO.output(self.gpio, True)

    def open(self):
        if self.actuator_polarity:
            GPIO.output(self.gpio, False)
        else:
            GPIO.output(self.gpio, True)
        if self.verbose:
            print(f"{datetime.now()}: DoorActuator: Activated")
        time.sleep(self.activation_time)
        if self.actuator_polarity:
            GPIO.output(self.gpio, True)
        else:
            GPIO.output(self.gpio, False)
        if self.verbose:
            print(f"{datetime.now()}: DoorActuator: Deactivated")

    def _thread(self):
        print("DoorActuator init")
        while True:
            data, topic = self.node.get()
            print(f"DoorActuator topic: {topic} -> message:{data}")
            if topic == self.topic:
                self.open()

    def start(self):
        self.thread.start()


class DoorSensor:
    def __init__(self, topic='door/sensor', pull_up=1, polarity=0, gpio=2, verbose=True):
        self.thread = threading.Thread(target=self._thread)
        self.gpio = gpio
        self.topic = topic
        self.polarity = polarity
        self.pull_up = pull_up
        self.node = YPubNode(topic)
        self.polarity = polarity
        self.verbose = verbose
        GPIO.setmode(GPIO.BCM)

        if self.pull_up:
            GPIO.setup(self.gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        else:
            GPIO.setup(self.gpio, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def _thread(self):
        print("DoorSensor init")
        sensor_state = GPIO.input(self.gpio)
        while True:
            if sensor_state != GPIO.input(self.gpio):
                sensor_state = GPIO.input(self.gpio)
                if sensor_state:
                    if self.polarity:
                        if self.verbose:
                            print("DoorSensor: Close")
                        self.node.post('close', self.topic)
                    else:
                        if self.verbose:
                            print("DoorSensor: Open")
                        self.node.post('open', self.topic)
                else:
                    if self.polarity:
                        if self.verbose:
                            print("DoorSensor: Open")
                        self.node.post('open', self.topic)
                    else:
                        if self.verbose:
                            print("DoorSensor: Close")
                        self.node.post('close', self.topic)
            time.sleep(0.5)

    def start(self):
        self.thread.start()


class MainDoorController:
    def __init__(self):
        self.thread = threading.Thread(target=self._thread)
        self.api = ApiConnector()
        self.pub_node = YPubNode()
        topic_list = ["door/barcode/in",
                      "door/barcode/out",
                      "door/sensor",
                      "door/button",
                      "door/masterbutton"]
        self.sub_node = YSubNode(topic=topic_list)

    def _thread(self):
        print("Main Door Controller Init")
        while True:
            message, topic = self.sub_node.get()
            if topic == 'door/barcode/in':
                dict_data = eval(message)
                print(dict_data['data']['identification'])
                r = self.api.open_door(dict_data['data']['identification'], 1)
                if json.loads(r.text)['is_valid']:
                    self.pub_node.post("open", "door/actuator")
            elif topic == 'door/barcode/out':
                dict_data = eval(message)
                print(dict_data['data']['identification'])
                r = self.api.open_door(dict_data['data']['identification'], 2)
                if json.loads(r.text)['is_valid']:
                    self.pub_node.post("open", "door/actuator")

    def start(self):
        self.thread.start()

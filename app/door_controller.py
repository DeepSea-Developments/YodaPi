try:
    import RPi.GPIO as GPIO
except:
    pass
import time
from scripts.ymq import YSubNode, YPubNode, YPubSubNode
import threading
from datetime import datetime
from app.api import ApiConnector


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
                print(message)
                print(message['identification'])
                r = self.api.open_door(message['identification'], 1)
                print(r)
                print(r.text)
            elif topic == 'door/barcode/out':
                print(message)
                print(message['identification'])
                r = self.api.open_door(message['identification'], 2)
                print(r)
                print(r.text)

    def start(self):
        self.thread.start()

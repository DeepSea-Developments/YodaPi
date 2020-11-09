try:
    import RPi.GPIO as GPIO
except Exception as e:
    print(e)
import time
from scripts.ymq import YSubNode, YPubNode, YPubSubNode
from scripts.barcode_reader import BarcodeType
import threading
from datetime import datetime
from app.api import ApiConnector
import json


class DoorActuator:
    def __init__(self, topic="door/actuator", actuator_polarity=0, activation_time=3, gpio=26, verbose=True):
        self.thread = threading.Thread(target=self._thread)
        self.gpio = gpio
        self.topic = topic
        self.node = YSubNode(topic)
        self.activation_time = activation_time
        self.actuator_polarity = actuator_polarity
        self.verbose = verbose

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.gpio, GPIO.OUT)
        if self.actuator_polarity:
            GPIO.output(self.gpio, GPIO.HIGH)

    def open(self):
        if self.actuator_polarity:
            GPIO.output(self.gpio, GPIO.LOW)
        else:
            GPIO.output(self.gpio, GPIO.HIGH)
        if self.verbose:
            print(f"{datetime.now()}: DoorActuator: Activated")
        time.sleep(self.activation_time)
        if self.actuator_polarity:
            GPIO.output(self.gpio, GPIO.HIGH)
        else:
            GPIO.output(self.gpio, GPIO.LOW)
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


class DoorButton:
    def __init__(self, topic='door/button', pull_up=1, polarity=0, gpio=3, verbose=True):
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
        print("DoorButton init")
        while True:
            if self.polarity:
                if GPIO.input(self.gpio):
                    if self.verbose:
                        print("DoorButton: pushed")
                    self.node.post('pushed', self.topic)
                    while GPIO.input(self.gpio):
                        time.sleep(0.5)
            else:
                if not GPIO.input(self.gpio):
                    if self.verbose:
                        print("DoorButton: pushed")
                    self.node.post('pushed', self.topic)
                    while not GPIO.input(self.gpio):
                        time.sleep(0.5)
            time.sleep(0.3)

    def start(self):
        self.thread.start()


class RemoteDoorControl:
    def __init__(self, polling_time_in_s = 20):
        self.sleep_time = polling_time_in_s
        self.thread = threading.Thread(target=self._thread)
        self.api = ApiConnector()
        self.pub_node = YPubNode()

    def _thread(self):
        print("RemoteDoorControl init")
        while True:
            r = self.api.door_status_verification()
            if json.loads(r.text)['is_open']:
                self.pub_node.post("open", "door/actuator")
                r = self.api.close_door()
            time.sleep(self.sleep_time)

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
        barcode_message = False
        while True:
            message, topic = self.sub_node.get()


            # -------------Open door if available barcode -------------
            if topic == 'door/barcode/in':
                door_dir = 1
                barcode_message = True
            elif topic == 'door/barcode/out':
                door_dir = 2
                barcode_message = True

            # -------------Open door if Button or master button pressed-------------
            elif topic == 'door/button':
                self.pub_node.post("open", "door/actuator")
            elif topic == 'door/masterbutton':
                self.pub_node.post("open", "door/actuator")

            # ------------- Evaluate barcode reading -------------
            if barcode_message:
                dict_data = eval(message)

                if "barcode_type" in dict_data.keys():
                    # ------------- Evaluate QR codes -------------
                    if dict_data["barcode_type"] == BarcodeType.QR.value:
                        print("Reading QR")
                        r = self.api.open_door(dict_data['data']['identification'],
                                               door_dir,
                                               dict_data["barcode_type"],
                                               dict_data["data"]["extra_txt"])
                        if json.loads(r.text)['is_valid']:
                            self.pub_node.post("open", "door/actuator")
                        else:
                            print(f"{dict_data['data']['name']} Not valid")
                    # ------------- Evaluate Cedula codes -------------
                    elif dict_data["barcode_type"] == BarcodeType.CEDULA_COLOMBIA.value:
                        print("Reading Cedula")
                        r = self.api.open_door(dict_data['data']['identification'],
                                               door_dir,
                                               dict_data["barcode_type"])
                        if json.loads(r.text)['is_valid']:
                            self.pub_node.post("open", "door/actuator")
                        else:
                            print(f"{dict_data['data']['name']} Not valid")
                barcode_message = False

    def start(self):
        self.thread.start()

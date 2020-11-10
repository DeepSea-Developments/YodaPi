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
from scripts.helpers import load_config
import json
import scripts.db as db
import app.models as models
import requests


class LocalDatabaseUpdater:
    def __init__(self, update_time_min = 60, auto_update_values=True):
        self.update_time_min = update_time_min
        self.auto_update_values = auto_update_values
        self.api = ApiConnector()
        self.thread = threading.Thread(target=self._thread)

    def _thread(self):
        print("LocalDatabaseUpdater init")
        while True:
            try:
                if self.auto_update_values:
                    self.update_time_min = int(load_config().get("local_db_update_min"))

                print("Checking if local database needs to be updated")

                db_session = db.SessionLocal()
                query = db_session.query(models.DBUpdateDate).first()
                r = self.api.get_last_db_change()

                remote_db_last_update = json.loads(r.text)["last_change"]

                update_db = False

                # Review if there if there is a local database
                if query is not None:
                    if query.last_update != remote_db_last_update:
                        print("Remote database changed")
                        query.last_update = remote_db_last_update
                        update_db = True
                        query = db_session.query(models.AuthUser).delete()

                # Create a new database
                else:
                    print("Database created for the fist time")
                    last_database_update = models.DBUpdateDate(remote_db_last_update)
                    db_session.add(last_database_update)
                    update_db = True

                if update_db:
                    r = self.api.get_database()
                    print(r.text)
                    for user in json.loads(r.text):
                        print(user)
                        auth_user = models.AuthUser(name=user["name"],
                                                    document=user["document"],
                                                    access_key=user["access_key"])
                        db_session.add(auth_user)

                db_session.commit()
                db_session.close()

                time.sleep(60 * self.update_time_min)
            except requests.exceptions.ConnectionError:
                print("Remote database check failed. No connection to server")
                time.sleep(6 * 15)
            except Exception as e:
                print("LocalDatabaseUpdater Error: ", e)
                time.sleep(60)

    def start(self):
        self.thread.start()


class DoorActuator:
    def __init__(self, topic="door/actuator", actuator_polarity=0, activation_time=3, auto_update_values=True, gpio=26, verbose=True):
        self.thread = threading.Thread(target=self._thread)
        self.gpio = gpio
        self.topic = topic
        self.node = YSubNode(topic)
        self.activation_time = activation_time
        self.actuator_polarity = actuator_polarity
        self.verbose = verbose
        self.auto_update_values = auto_update_values

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.gpio, GPIO.OUT)
        if self.actuator_polarity:
            GPIO.output(self.gpio, GPIO.HIGH)

    def open(self):
        # Review if Activation time is None
        if self.auto_update_values:
            self.activation_time = int(load_config().get("actuator_time"))
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
            try:
                data, topic = self.node.get()
                print(f"DoorActuator topic: {topic} -> message:{data}")
                if topic == self.topic:
                    self.open()
            except Exception as e:
                print("Door actuator error: ",e)
                time.sleep(1)

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
            try:
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
            except Exception as e:
                print("DoorSensor error: ", e)
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
            try:
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
            except Exception as e:
                print("DoorButton error:", e)
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
            try:
                r = self.api.door_status_verification()
                if json.loads(r.text)['is_open']:
                    self.pub_node.post("open", "door/actuator")
                    time.sleep(0.1)
                    self.pub_node.post("open", "door/buzzer/long_buzz")
                    r = self.api.close_door()
            except requests.exceptions.ConnectionError:
                print("RemoteDoorControl failed. No connection to server")
            except Exception as e:
                print("Remote Door Control error: ", e)
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
            try:
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
                    self.pub_node.post("authorized", "door/buzzer/long_buzz")
                elif topic == 'door/masterbutton':
                    self.pub_node.post("open", "door/actuator")
                    self.pub_node.post("authorized", "door/buzzer/long_buzz")

                # ------------- Evaluate barcode reading -------------
                if barcode_message:
                    dict_data = eval(message)

                    if "barcode_type" in dict_data.keys():
                        # ------------- config params of QR codes -------------
                        if dict_data["barcode_type"] == BarcodeType.QR.value:
                            print("Reading QR")
                            barcode_params = {'document': dict_data['data']['identification'],
                                              'door_dir': door_dir,
                                              'barcode_type': dict_data["barcode_type"],
                                              'qr_code': dict_data["data"]["extra_txt"]}
                        # ------------- config params of  Cedula codes -------------
                        elif dict_data["barcode_type"] == BarcodeType.CEDULA_COLOMBIA.value:
                            print("Reading Cedula")
                            barcode_params = {'document': dict_data['data']['identification'],
                                              'door_dir': door_dir,
                                              'barcode_type': dict_data["barcode_type"]}
                        # -------------- Evaluate barcodes -----------------

                        try:
                            r = self.api.open_door(**barcode_params)
                            if json.loads(r.text)['is_valid']:
                                self.pub_node.post("open", "door/actuator")
                                self.pub_node.post("authorized", "door/buzzer/long_buzz")
                            else:
                                print(f"{barcode_params['name']} Not valid")
                                self.pub_node.post("unauthorized", "door/buzzer/two_short_buzzes")
                        except requests.exceptions.ConnectionError:
                            # Could not connect to cloud. Trying local database
                            db_session = db.SessionLocal()
                            query = db_session.query(models.AuthUser).filter_by(document=barcode_params['document']).first()
                            print(query)
                            if query:
                                self.pub_node.post("open", "door/actuator")
                        except Exception as e:
                            print("MainDoor controller. Validating barcode error: ", e)

                    barcode_message = False
            except Exception as e:
                print("controller error: ", e)
                time.sleep(1)

    def start(self):
        self.thread.start()


class Buzzer:
    def __init__(self, topic="door/buzzer", buzzer_polarity=0, activation_time=3, auto_update_values=True, gpio=13, verbose=True):
        self.thread = threading.Thread(target=self._thread)
        self.gpio = gpio
        self.topic = topic
        self.node = YSubNode(topic)
        self.activation_time = activation_time
        self.actuator_polarity = buzzer_polarity
        self.verbose = verbose
        self.auto_update_values = auto_update_values

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.gpio, GPIO.OUT)
        if self.actuator_polarity:
            GPIO.output(self.gpio, GPIO.HIGH)

    def buzz(self, buzz_time):

        if self.actuator_polarity:
            GPIO.output(self.gpio, GPIO.LOW)
        else:
            GPIO.output(self.gpio, GPIO.HIGH)

        time.sleep(buzz_time)

        if self.actuator_polarity:
            GPIO.output(self.gpio, GPIO.HIGH)
        else:
            GPIO.output(self.gpio, GPIO.LOW)

    def long_buzz(self):
        # Review if Activation time is None
        if self.auto_update_values:
            self.activation_time = int(load_config().get("actuator_time"))

        if self.verbose:
            print(f"{datetime.now()}: Buzzer: Activated")
        self.buzz(self.activation_time)
        if self.verbose:
            print(f"{datetime.now()}: Buzzer: Deactivated")

    def two_short_buzzes(self):

        if self.verbose:
            print(f"{datetime.now()}: Buzzer: Activated")
        self.buzz(0.5)
        time.sleep(0.5)
        self.buzz(0.5)
        if self.verbose:
            print(f"{datetime.now()}: Buzzer: Deactivated")

    def _thread(self):
        print("Buzzer init")
        while True:
            try:
                data, topic = self.node.get()
                print(f"Buzzer topic: {topic} -> message:{data}")
                if topic == self.topic + "/long_buzz":
                    self.long_buzz()
                elif topic == self.topic + "/two_short_buzzes":
                    self.two_short_buzzes()
            except Exception as e:
                print("Door Buzzer error: ", e)
                time.sleep(1)

    def start(self):
        self.thread.start()
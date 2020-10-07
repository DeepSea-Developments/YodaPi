try:
    import RPi.GPIO as GPIO
except:
    pass
from scripts.ymq import YPubNode, YSubNode
import time
from scripts.ymq import YSubNode, YPubNode
import threading


class DoorActuator:
    def __init__(self, topic, actuator_polarity=0, activation_time=3, gpio=26):
        self.gpio = gpio
        self.node = YSubNode(topic)
        self.activation_time = activation_time
        self.actuator_polarity = actuator_polarity
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio, GPIO.OUT)
        if self.actuator_polarity:
            GPIO.output(self.gpio, True)

    def open(self):
        if self.actuator_polarity:
            GPIO.output(self.gpio, False)
        else:
            GPIO.output(self.gpio, True)
        time.sleep(self.actvation_time)
        if self.actuator_polarity:
            GPIO.output(self.gpio, True)
        else:
            GPIO.output(self.gpio, False)

    def _thread(self):
        while True:
            data, topic = self.node.get()
            print(f"DoorActuator topic: {topic} -> message:{data}")
            if (topic == self.topic):
                self.open()

    def start(self):
        self.thread = threading.Thread(target=self._thread)
        self.thread.start()

#
# counter = 0
# x = ""
#
# while 1:
#
#     if (ser.in_waiting > 0):
#         x = ser.readline().decode()
#         print(x)
#
#     if (ser2.in_waiting > 0):
#         x = ser2.readline().decode()
#         print(x)
#     if (x == "GA26923"):
#         print("OPEN")
#         GPIO.output(trigger, True)
#         time.sleep(2.5)
#         GPIO.output(trigger, False)
#         x = ""

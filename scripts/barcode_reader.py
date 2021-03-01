import sys
import os

import json
import re
import threading
import lzstring
#import requests
import serial
from enum import Enum
from time import sleep
from datetime import datetime
from scripts.helpers import get_args, get_ports, get_port_by_port_location
from scripts.ymq import YPubNode
import base64

class Person:
    def __init__(self, identification=None, name=None, last_name=None, gender=None, birth_date=None, blood_type=None,
                 extra_json=None, extra_txt=None, alert=None):
        self.identification = identification
        self.name = name
        self.last_name = last_name
        self.gender = gender
        self.birth_date = birth_date
        self.blood_type = blood_type
        self.extra_json = extra_json
        self.extra_txt = extra_txt
        self.alert = alert

    @staticmethod
    def append_names(name1, name2):
        names = [name1, name2]
        return ' '.join(filter(None, names))


class BarcodeType(Enum):
    QR = 0
    CEDULA_COLOMBIA = 1
    CEDULA_COSTA_RICA = 2
    QR_DSD = 3


class BarcodeReader:
    ports_allowlist = [44953]

    KEYS_ARRAY_CR = [0x27, 0x30, 0x04, 0xA0, 0x00, 0x0F, 0x93, 0x12, 0xA0, 0xD1, 0x33, 0xE0, 0x03, 0xD0, 0x00, 0xDf,
                     0x00]
    thread = None
    initiated = False
    args = None

    def __init__(self, port=None, port_location=None, baudrate=115200, topic=""):

        self.port_location = port_location
        self.baudrate = baudrate

        if port_location is not None:
            port = get_port_by_port_location(self.port_location)

        if port is None:
            ports = get_ports()
            for (com, desc, vid) in zip(ports[0], ports[1], ports[2]):
                # print(com, desc, vid)
                if vid in BarcodeReader.ports_allowlist:
                    port = com
        else:
            try:
                self.serial = serial.Serial(port=port, baudrate=baudrate, timeout=0.5)
                self.initiated = True
            except Exception as e:
                print(e)
            self.args = get_args()

        self.node = YPubNode(topic)

    def __del__(self):
        self.serial.close()

    @staticmethod
    def _decode_string_utf_8(values):
        string_data = ''
        for data in values:
            if data != b'\x00':
                string_data = string_data + data.decode('utf-8')
        return string_data

    @staticmethod
    def _decode_string_iso_8859_1(values):
        string_data = ''
        for data in values:
            if data != b'\x00':
                string_data = string_data + data.decode('iso-8859-1')
        return string_data

    def get_reading(self):

        if self.serial.in_waiting > 0:
            msg = []
            data_size = self.serial.in_waiting
            for i in range(data_size):
                value = self.serial.read()
                msg.append(value)

            # TODO improve code type detection  to allow qr codes of length 531 and 700
            if len(msg) == 531:
                code_type = BarcodeType.CEDULA_COLOMBIA
            elif len(msg) == 700:
                code_type = BarcodeType.CEDULA_COSTA_RICA
            else:
                code_type = BarcodeType.QR

            try:
                data = None
                if code_type == BarcodeType.CEDULA_COLOMBIA:
                    person = Person(
                        identification=self._decode_string_iso_8859_1(msg[48:58]).lstrip('0'),
                        name=Person.append_names(self._decode_string_iso_8859_1(msg[104:127]),
                                                 self._decode_string_iso_8859_1(msg[127:150])),
                        last_name=Person.append_names(self._decode_string_iso_8859_1(msg[58:81]),
                                                      self._decode_string_iso_8859_1(msg[81:104])),
                        gender=self._decode_string_iso_8859_1(msg[151:152]),
                        birth_date=self._decode_string_iso_8859_1(msg[152:156]) + '-' + self._decode_string_iso_8859_1(
                            msg[156:158]) + '-' + self._decode_string_iso_8859_1(msg[158:160]),
                        blood_type=self._decode_string_iso_8859_1(msg[166:169])
                    )
                    data = person.__dict__

                elif code_type == BarcodeType.CEDULA_COSTA_RICA:
                    d = ""
                    j = 0
                    count = 0
                    for _value in msg:
                        if j == 17:
                            j = 0
                        # __value = int(_value)
                        c = self.KEYS_ARRAY_CR[j] ^ _value[0]
                        if re.match("^[a-zA-Z0-9]*$", chr(c)):
                            d = d + chr(c)
                            count = count + 1
                        else:
                            d += ' '
                        j = j + 1

                    person = Person(
                        identification=d[0:9].strip(),
                        name=d[61:91].strip(),
                        last_name=Person.append_names(d[9:35].strip(), d[35:61].strip()),
                    )
                    data = person.__dict__

                elif code_type == BarcodeType.QR:
                    # This implementations expects QR codes in json format, encoded in base 64
                    base64_data = (''.join(self._decode_string_iso_8859_1(msg)))
                    print(base64_data)
                    decoded_data = base64.b64decode(base64_data).decode('utf-8')
                    try:
                        msg_json = json.loads(decoded_data)
                    except Exception as e:
                        print("Error. Not a valid json. error:", e)
                    person = Person(
                        name=msg_json["name"],
                        identification=msg_json["document"],
                        extra_txt=json.dumps(msg_json)
                    )
                    data = person.__dict__
                if data is not None:
                    return {
                        'barcode_type': code_type.value,
                        'data': data,
                        'timestamp': datetime.now().isoformat()
                    }
            except Exception as e:
                print("Bardcode Error: ",e)
                return
        else:
            sleep(0.1)

    def _thread(self):
        while True:
            try:
                reading = self.get_reading()
                if reading:
                    self.node.post(reading)
            except Exception as e:
                print(e)
                print("Serial disconnected. Trying to reconnect")
                sleep(1)
                try:
                    self.serial.close()
                except Exception as e:
                    pass

                try:
                    port = get_port_by_port_location(self.port_location)
                    self.serial = serial.Serial(port=port, baudrate=self.baudrate, timeout=0.5)
                    self.initiated = True
                except Exception as e:
                    print(e)

    def start(self):
        """Start the background simulator thread if it isn't running yet."""
        if self.thread is None:
            # start background frame thread
            self.thread = threading.Thread(target=self._thread)
            self.thread.start()

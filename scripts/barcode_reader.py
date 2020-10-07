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
from scripts.helpers import get_args, get_ports
from scripts.ymq import YPubNode

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

    def __init__(self, port=None, baudrate=115200, topic=""):
        if port is None:
            ports = get_ports()
            for (com, desc, vid) in zip(ports[0], ports[1], ports[2]):
                # print(com, desc, vid)
                if vid in BarcodeReader.ports_allowlist:
                    port = com

        if port is not None:
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
        # msg = self.serial.readline()
        # if msg:

        if self.serial.in_waiting > 0:
            msg = []
            data_size = self.serial.in_waiting
            for i in range(data_size):
                value = self.serial.read()
                msg.append(value)
            # print(msg)
            # print(len(msg))

            # msg = [msg[i:i + 1] for i in range(0, len(msg), 1)]

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
                    decoded_data = (''.join(self._decode_string_iso_8859_1(msg)))

                    if decoded_data.startswith('DSD:'):
                        code_type = BarcodeType.QR_DSD
                        x = lzstring.LZString()
                        base64data = decoded_data[4:]
                        json_string = x.decompressFromBase64(base64data)

                        data_dict = json.loads(json_string)
                        identification = data_dict['id']
                        name = data_dict['fn']
                        last_name = data_dict['ln']

                        data_dict.pop('id', None)
                        data_dict.pop('fn', None)
                        data_dict.pop('ln', None)

                        alert = False
                        for key in data_dict:
                            if key.startswith('r'):
                                response_number = key[1:]
                                alert_key = 'a' + response_number
                                if alert_key in data_dict and data_dict[alert_key] == data_dict[key]:
                                    alert = True
                                    break

                        person = Person(
                            identification=identification,
                            name=name,
                            last_name=last_name,
                            extra_json=data_dict,
                            alert=alert
                        )
                        data = person.__dict__

                    elif self.args.qrexternal:
                        person = Person(
                            extra_txt=decoded_data
                        )
                        data = person.__dict__

                if data is not None:
                    return {
                        'barcode_type': code_type.value,
                        'data': data,
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    print('External QR not enabled')
                    return None
            except Exception as e:
                print(e)
                return
        else:
            sleep(0.1)

    def _thread(self):
        while True:
            reading = self.get_reading()
            if reading:
                #requests.post('http://127.0.0.1:8080/barcode_scan', json=reading)
                self.node.post(reading)

    def start(self):
        """Start the background simulator thread if it isn't running yet."""
        if self.thread is None:
            # start background frame thread
            self.thread = threading.Thread(target=self._thread)
            self.thread.start()

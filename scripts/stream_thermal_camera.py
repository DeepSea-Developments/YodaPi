import sys
import os

import time
import socket
import pickle
import serial
import threading
import re

from scripts.m80_rpi import M80
from datetime import datetime


class StreamThermalCamera:
    thread = None

    OPC_DELTA_TEMP = 0.5
    OPC_TIMEOUT = (30 * 60)
    # OPC_TIMEOUT = (10)

    initial_program_time = datetime.now()
    last_time = datetime.now()
    # time.sleep(1)
    current_time = datetime.now()
    difference = current_time - last_time

    UDP_IP = "127.0.0.1"
    UDP_PORT = 5001

    cam = None
    base_temp = None
    serial_port = None
    serial_mcu = None

    def __init__(self, serial_port):
        self.serial_port = serial_port
        print("Attemping connection to Serial MCU")

        try:
            self.serial_mcu = serial.Serial(self.serial_port, 57600)
        except Exception as e:
            print("Error at opening serial: ", e)
            return
        # time.sleep(1)

        self.serial_mcu.write(b'start\n')
        print("Attemping connection to M80 camera")
        try:
            self.cam = M80()
            # self.cam.OPC()
            # self.cam.start_video_TBP()
        except Exception as e:
            print("Error at opening M80: ", e)
            self.serial_mcu.close()

        self.serial_mcu.flushInput()

        try:
            print("Doing OPC")
            self.termodeep_opc()
            self.cam.start_video_TBP()
            self.cam.get_frame()
            self.cam.get_frame()
            if self.cam.temp < 100 and self.cam.temp > 0:
                self.base_temp = self.cam.temp
            else:
                self.base_temp = 30
            print("Initial Temp: {}".format(self.base_temp))

        except Exception as e:
            print("Error at init rutine: ", e)
            self.serial_mcu.close()
            self.cam.terminate()
            return

    def termodeep_opc(self):
        self.serial_mcu.write(b'close\n')
        time.sleep(0.2)
        self.cam.OPC()
        time.sleep(0.2)
        self.serial_mcu.write(b'open\n')
        print("OPC Complete")

    def _thread(self):
        """Camera stream background thread."""
        sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_DGRAM)  # UDP

        run_main = True
        print('Starting camera stream thread.')
        get_number = re.compile(r'(\d+\.?\d*)')
        while run_main and self.cam:

            try:
                time.sleep(0.1)
                image = self.cam.get_frame()
                msg = pickle.dumps(image)

                sock.sendto(msg, (self.UDP_IP, self.UDP_PORT))

                cam_temp_diff = abs((self.cam.temp - self.base_temp))
                difference = datetime.now() - self.last_time

                # self.serial_mcu.write(b'temp?\n')
                # time.sleep(0.5)
                # match = get_number.search(self.serial_mcu.read_all().decode("utf-8"))
                # if match:
                #     bb_temp = match.group(0)
                #     print(bb_temp)


                # time.sleep(0.5)
                # self.serial_mcu.write(b'status\n')
                # print(self.serial_mcu.read_all().decode("utf-8"))


                if ((cam_temp_diff > self.OPC_DELTA_TEMP) and (
                        cam_temp_diff < 60)) or difference.seconds > self.OPC_TIMEOUT:
                    print("{}------OPC at temp {} c ------".format(datetime.now(), self.cam.temp))

                    self.base_temp = self.cam.temp
                    self.last_time = datetime.now()
                    self.cam.stop_video()
                    self.termodeep_opc()
                    time.sleep(1)
                    self.serial_mcu.write(b'start\n')
                    self.cam.start_video_TBP()
            except KeyboardInterrupt:
                run_main = False
                time.sleep(5)
                # self.serial_mcu.close()

            except serial.SerialTimeoutException as e:
                print("Serial Timeout exception")

            except Exception as e:
                print('Man Loop Error: ', e)
                time.sleep(10)

    def start(self):
        """Start the background simulator thread if it isn't running yet."""
        if self.thread is None:
            # start background frame thread
            self.thread = threading.Thread(target=self._thread)
            self.thread.start()

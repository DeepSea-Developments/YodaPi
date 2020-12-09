# -*- coding: utf-8 -*-
"""
M80 library for Raspberry pi

Created on May  31 2020

@author: ElectroNick
"""

import time
import numpy as np

import spidev
from gpiozero import InputDevice, OutputDevice
from datetime import datetime
from enum import Enum

from PIL import Image

# SPI Protocol definitions

START_FRAME_1BP = [0x7E, 0x01, 0x07, 0x00, 0x00, 0x00]
START_FRAME_2BP = [0x7E, 0x01, 0x07, 0x01, 0x00, 0x00]
START_FRAME_2BR = [0x7E, 0x01, 0x07, 0x02, 0x00, 0x00]
READ_GAIN = [0x7E, 0x01, 0x05, 0x00, 0x00, 0x00]
SET_GAIN = [0x7E, 0x01, 0x05, 0x01, 0x00, 0x00]
READ_OFFSET = [0x7E, 0x01, 0x06, 0x00, 0x00, 0x00]
SET_OFFSET = [0x7E, 0x01, 0x06, 0x01, 0x00, 0x00]
READ_VERSION = [0x7E, 0x01, 0x0A, 0x00, 0x00, 0x00]
CAMERA_OPC_CMD = [0x7E, 0x01, 0x01, 0x00, 0x00, 0x00]
STOP_FRAME = [0x7E, 0x01, 0x08, 0x00, 0x00, 0x00]
RESPONSE_FRAME = [0x7E, 0x02, 0x07, 0x00, 0x00, 0x00]
READ_VTEMP = [0x7E, 0x01, 0xEE, 0x00, 0x00, 0x00]
SOFTWARE_RESET = [0x7E, 0x01, 0xF5, 0x00, 0x00, 0x00]


# There will be 3 verbose levels
# 0  mean no print at all
# 1  mean just text prints
# 3  mean  text and hex values of single commands interchanges

class VideoMode(Enum):
    OBP = 0
    TBP = 1
    TBR = 2


class VideoStatus(Enum):
    IDLE = 0
    RUNNING = 1


class VerboseLevel(Enum):
    NONE = 0
    BASIC = 1
    ADVANCED = 2


class M80:
    """wait the interruption pin into the available status

    Args:
        timeout_s (int): timeout in seconds
    Returns:
        None
    """

    def __init__(self, spi_bus=0, spi_device=0, spi_freq=12000000, verbose_level=VerboseLevel.NONE):

        # -------------------Hardware modules init------------------------

        # Instanciate a SPI controller. 
        self.spi = spidev.SpiDev()

        # Open SPI device
        self.spi.open(spi_bus, spi_device)

        # Configure SPI speed
        self.spi.max_speed_hz = spi_freq

        # Init interrup pin
        self.int_pin = InputDevice("GPIO6")
        self.reset_pin = OutputDevice("GPIO5")
        self.reset_pin.on()

        # -------------------Private variables definition------------------

        self.video_mode = VideoMode.OBP
        self.video_status = VideoStatus.IDLE
        self.verbose_level = verbose_level

        self.video_data_size = 6400

        self.serial = (0, 0, 0)
        self.temp_raw = 0
        self.temp = 0

        self.brightness_live_change = False
        self.contrast_live_change = False

        self.brightness_live_value = 0
        self.contrast_live_value = 0

    # --------------------------------------------Base hardware functions------------------------------------

    def _read_int_pin(self):
        return bool(self.int_pin.value)

    def _spi_read(self, bytes):
        return self.spi.readbytes(bytes)

    def _spi_write(self, w_data):
        self.spi.writebytes(w_data)

    # def _spi_readwrite(self, rw_data):
    #    a = rw_data
    #    return self.spi.xfer(a) #DO NOT USE XFER! NEVER! EVER!! NEVER EVER!!

    def _spi_close(self):
        self.spi.close()

    # --------------------------------------------Auiliar functions------------------------------------
    def _print_hex(self, data):
        if self.verbose_level.value >= VerboseLevel.ADVANCED.value:
            print([hex(x) for x in data])

    def _print_debug(self, data):
        if self.verbose_level.value >= VerboseLevel.BASIC.value:
            print(data)

    def _temperature_calculation(self, raw_temp):
        return 475 - (582.4 * raw_temp) / 16384

    # --------------------------------------------Camera functions------------------------------------

    def _wait_int(self, timeout_s=30):
        """wait the interruption pin into the available status

        Args:
            timeout_s (int): timeout in seconds
        Returns:
            None
        """
        start_tick = datetime.now()
        while (not (self._read_int_pin()) and ((datetime.now() - start_tick).seconds) < timeout_s):
            time.sleep(0.05)
            # print('.', end='')
        if not self._read_int_pin():
            self._print_debug("Wait int timeout")

    def read_serial(self):
        """Reads the serial of the device. 

        Args:
            file_loc (str): The file location of the spreadsheet
            print_cols (bool): A flag used to print the columns to the console
                (default is False)

        Returns:
            list: 3 numbers conforming the serial
        """
        self._print_debug("----------read_serial---------")
        if self.video_status == VideoStatus.IDLE:
            self._wait_int()
            self._spi_write(READ_VERSION)
            self._wait_int()
            read_buff = self._spi_read(6)
            self._print_hex(read_buff)
            self._wait_int()
            read_buff = self._spi_read(6)

            self._print_hex(read_buff)
            self._wait_int()
            self.serial = ((read_buff[1] << 8) + read_buff[0],  # NB1
                           (read_buff[3] << 8) + read_buff[2],  # NB2
                           (read_buff[5] << 8) + read_buff[4])  # NB3
            return self.serial
        else:
            return self.serial

    def read_temp(self):
        self._print_debug("----------read_temp---------")
        if self.video_status == VideoStatus.IDLE:
            self._wait_int()
            self._spi_write(READ_VTEMP)
            self._wait_int()
            read_buff = self._spi_read(6)
            self._print_hex(read_buff)
            self.temp_raw = read_buff[4] << 8 | read_buff[5]
            self.temp = self._temperature_calculation(self.temp_raw)
            return self.temp
        else:
            self.temp = self._temperature_calculation(self.temp_raw)
            return self.temp

    def terminate(self):
        self._print_debug("----------Terminate---------")
        self._spi_close()
        self._print_debug("M80 says bye bye")

    def OPC(self, iteration_number=50):
        self._print_debug("----------OPC---------")
        rerun_flag = False
        if self.video_status == VideoStatus.RUNNING:
            rerun_flag = True
            self.stop_video()
            time.sleep(0.2)
        self._wait_int()
        self._spi_write(CAMERA_OPC_CMD[:-2] + [iteration_number >> 8] + [iteration_number & 0xFF])
        self._wait_int()
        read_buff = self._spi_read(6)
        self._print_hex(read_buff)

        if rerun_flag:
            time.sleep(0.2)
            self.start_video(self.video_mode)

    def stop_video(self):
        self._print_debug("----------Stop Video---------")
        self._wait_int()
        self._print_hex(STOP_FRAME)
        self._spi_write(STOP_FRAME)
        time.sleep(1)
        self._wait_int()

        self.video_status = VideoStatus.IDLE

    def start_video_OBP(self):
        self._print_debug("----------Start Video OPB---------")
        self.start_video(VideoMode.OBP)

    def start_video_TBP(self):
        self._print_debug("----------Start Video TBP---------")
        self.start_video(VideoMode.TBP)

    def start_video_TBR(self):
        self._print_debug("----------Start Video TBR---------")
        self.start_video(VideoMode.TBR)

    def start_video(self, video_mode):

        self._print_debug("----------Start Video---------")

        # If video is runnung and the same video mode is requested, just ignore the command
        if self.video_status == VideoStatus.RUNNING and self.video_mode == video_mode:
            return
        # If video is running and another video mode is requested, stop the current video mode and start a new one.
        elif self.video_status == VideoStatus.RUNNING:
            self.stop_video()

        # Update video mode and status
        self.video_mode = video_mode
        self.video_status = VideoStatus.RUNNING

        # Choose the right start frame and the size of the data
        if video_mode == VideoMode.OBP:
            frame_start = START_FRAME_1BP
            self.video_data_size = 6400
        elif video_mode == VideoMode.TBP:
            frame_start = START_FRAME_2BP
            self.video_data_size = 12800
        else:
            frame_start = START_FRAME_2BR
            self.video_data_size = 12800

        # Send Start Frame
        self._wait_int()
        self._spi_write(frame_start)

        # Receive Response Frame
        self._wait_int()
        read_buff = self._spi_read(6)
        self._print_hex(read_buff)
        self._wait_int()

        # Validate if response frame is correct
        if read_buff[0:3] == RESPONSE_FRAME[0:3]:
            read_buff = self._spi_read(self.video_data_size)
            # self._print_hex(read_buff)
            # print(len(read_buff))
            self.temp_raw = read_buff[4] << 8 | read_buff[5]
            # print(self.temp_raw)
            self.temp = self._temperature_calculation(self.temp_raw)
        else:
            self._print_debug("start_video -M80 streaming error. Response:")
            self._print_hex(read_buff)
            # raise Exception("start_2BP_frame -M80 streaming error")

    def get_frame(self):
        self._print_debug("----------Get Frame---------")

        FrameMatrix = np.zeros((80, 80))
        if self.video_status == VideoStatus.IDLE:
            self._print_debug("Video is stopped. Can't acquire frames")
            return FrameMatrix

        # Read command frame
        self._wait_int()
        read_buff = self._spi_read(6)
        self._wait_int()

        counter = 0
        i = 0
        j = 0

        # Verify if is good
        if read_buff[0:3] == RESPONSE_FRAME[0:3]:
            self._print_hex(read_buff)
            # Get current temperature value
            self.temp_raw = read_buff[4] << 8 | read_buff[5]
            # print(self.temp_raw)
            self.temp = self._temperature_calculation(self.temp_raw)
            read_buff = self._spi_read(self.video_data_size)
            aux_state = 0

            for position in range(6400):
                if self.video_mode == VideoMode.OBP:
                    pixel = read_buff[position]
                else:
                    pixel = read_buff[2 * position] | read_buff[2 * position + 1] << 8

                FrameMatrix[i][j] = pixel

                j = j + 1
                if j == 80:
                    j = 0
                    i = i + 1
        else:
            print("get_frame -M80 streaming error. Response:")
            self._print_hex(read_buff)

        return FrameMatrix

    def take_snapshot(self, file='img.png'):

        self._print_debug("----------Take Snapshot---------")

        # First review current status of the camera
        if self.video_status == VideoStatus.RUNNING:
            frame = self.get_frame()
            if self.video_mode != VideoMode.OBP:
                # Have to scale the image to be shown correctly
                frame = frame - frame.min()
                frame = frame / frame.max()
        else:
            self.start_video(VideoMode.OBP)
            frame = self.get_frame()
            self.stop_video()

        # Turn the frame into a 8 bit per pixel mode
        frame = frame.astype(np.uint8)
        img = Image.fromarray(frame, 'L')
        img.save(file)

    def reset(self):
        self._print_debug("----------Hardware Reset---------")
        self.reset_pin.off()
        time.sleep(1)
        self.reset_pin.on()
        time.sleep(1)

import sys
import os

import cv2
import socket
import pickle
import configparser

from scripts.helpers import get_args, load_config
from scripts.base_camera import BaseCamera
from scripts.opencv_processing import OpenCVProcessor


class CameraThermal(BaseCamera):

    @staticmethod
    def frames():
        sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_DGRAM)  # UDP
        sock.bind(("127.0.0.1", 5001))

        print('Creating OpenCV Processor ...')

        #Use a config file
        conf = load_config()
        
        args = get_args()

        processor = OpenCVProcessor(args.calibrating)
        processor.REF_TEMP = float(conf.get('REF_TEMP'))
        processor.CAM_SENSITIVITY = float(conf.get('CAM_SENSITIVITY'))
        processor.THRESHOLD_HUMAN_TEMP = float(conf.get('THRESHOLD_HUMAN_TEMP'))

        while True:
            data, addr = sock.recvfrom(1024 * 64)  # buffer size is 1024 bytes

            frame_raw = pickle.loads(data)

            img_large, temperatures = processor.process_frame(frame_raw)

            frame = {
                'thermal_image': cv2.imencode('.png', img_large)[1].tobytes(),
                'temperatures': temperatures
            }

            yield frame

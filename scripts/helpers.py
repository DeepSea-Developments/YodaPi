import sys
import os
import argparse
import logging
import sys
import uuid
import configparser
import threading
import pathlib

from serial.tools.list_ports import comports

# Set stop signal - camera thread
global stop_camera_thread
stop_camera_thread = threading.Event()

DEFAULT_CONFIG_PATH = pathlib.Path(__file__).parent / '../conf/yodapi.ini'

def get_args():
    parser = argparse.ArgumentParser(description='Start Flask Server.')
    parser.add_argument("-c", "--config-path", help="Path of the configuration file", type=str)
    parser.add_argument("-d", "--db-path", help="Path of the database", type=str)
    parser.add_argument("-p", "--port", help="Flask port", type=int)

    parser.add_argument("-z", "--cloud", help="Upload data to cloud", action="store_true")
    parser.add_argument("-u", "--simulator", help="Simulate the RPI", action="store_true")

    return parser.parse_args()


def get_mac():
    mac_num = hex(uuid.getnode()).replace('0x', '').upper()
    mac = '-'.join(mac_num[i: i + 2] for i in range(0, 11, 2))
    return mac


def disable_logging():
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    log.disabled = True

    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None


def get_ports():
    port_device = []
    port_description = []
    port_vid = []

    for port in comports():
        port_device.append(port.device)
        port_description.append(port.description)
        port_vid.append(port.vid)

    ports = (port_device, port_description, port_vid)
    return ports


def load_config(debug=True):
    '''
    Load the configurations of the project
    '''
    config_path = DEFAULT_CONFIG_PATH
    if not debug:
        args = get_args()
        if args.config_path:
            config_path = args.config_path

    config = configparser.ConfigParser()

    # If file doesn't exist, create config file
    if not os.path.exists(config_path):
        # todo write the default configurations
        config['DEFAULT'] = {'test': '45', 'test2': 'yes'}
        config.write(open(config_path, 'w'))

    config.read(config_path)

    if 'CUSTOM' in config:
        conf = config['CUSTOM']
    else:
        conf = config['DEFAULT']

    return conf


def get_parameters_id_list(params):
    param_list = []
    for tab in params:
        for section in tab['tab_data']:
            for field in section['section_data']:
                param_list.append(field['param_id'])
    return param_list

import threading
import os
import re
import sentry_sdk

from scripts.barcode_reader import BarcodeReader
from scripts.cloud_synchronizer import CloudSynchronizer
from scripts.helpers import get_args, disable_logging, load_config
from yodapi_flask import flask_main
from app.door_controller import DoorActuator, MainDoorController

import scripts.models
import scripts.db as db
from scripts.ymq import YServer

# def start_stream():
#     from scripts.stream_thermal_camera import StreamThermalCamera
#     thermal_camera_stream = StreamThermalCamera("/dev/ttyS0")
#     thermal_camera_stream.start()


yodapi_header = '''
----------------------------------------------------
Y88b   d88P            888          8888888b.  d8b 
 Y88b d88P             888          888   Y88b Y8P 
  Y88o88P              888          888    888     
   Y888P  .d88b.   .d88888  8888b.  888   d88P 888 
    888  d88""88b d88" 888     "88b 8888888P"  888 
    888  888  888 888  888 .d888888 888        888 
    888  Y88..88P Y88b 888 888  888 888        888 
    888   "Y88P"   "Y88888 "Y888888 888        888  
----------------------------------------------------
Open Source! Yeah!
any questions? write me at nick@dsd.dev                                             
'''

pc_mode = '''
----------------------------------------------------
 __  __              
|__)/     _  _  _| _ 
|   \__  |||(_)(_|(- 
----------------------------------------------------
'''





if __name__ == '__main__':
    # Print YodaPi Header
    print(yodapi_header)

    # Get args (might be deprecated soon. don't kno yet)
    args = get_args()

    # Load configurations
    conf = load_config()

    # Disable flask logging info. You can comment this if want to debug flask's messages
    disable_logging()

    # Review if running on PC or in Raspberry, to run in simulator mode or not
    os_info = os.uname()
    if not (re.search(r'arm', os_info[4])):
        args.simulator = True

    # Init Database
    if args.db_path:
        db.init(conf.get(args.db_path))
    else:
        db.init(conf.get('db_path'))

    yserver = YServer(verbose=True)
    yserver.start()

    if not args.simulator:  # Use in RPI
        #sentry_sdk.init(conf.get("sentry_url"))
        #start_stream()

        door_actuator = DoorActuator("door/actuator")
        door_actuator.start()

    else:  # Use in Computer
        print(pc_mode)

    if args.port:
        flask_thread = threading.Thread(target=flask_main, args=[args.port])
    else:
        flask_thread = threading.Thread(target=flask_main)
    flask_thread.start()

    # # Cloud synchronizer
    # if args.cloud:
    #     cloud = CloudSynchronizer()
    #     cloud.start()

    barcode_in = BarcodeReader(topic="door/barcode/in", port="/dev/ttyACM0")
    barcode_out = BarcodeReader(topic="door/barcode/out", port="/dev/ttyACM1")

    if barcode_in.initiated:
        barcode_in.start()
    if barcode_out.initiated:
        barcode_out.start()

    main_door_controller = MainDoorController()
    main_door_controller.start()
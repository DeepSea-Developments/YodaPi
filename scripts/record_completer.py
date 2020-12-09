import sys
import os

import sqlite3
from datetime import datetime, timedelta
from io import BytesIO

from scripts.cloud_synchronizer import upload_record_by_id
from scripts.helpers import get_args, load_config
from scripts.camera_thermal import CameraThermal
from scripts.database import DATABASE
import scripts.camera_rgb


class RecordCompleter():
    thread = None
    record_id = None
    db = None

    DELAY = 1
    ALERT_WARNING_TEMP = 37.5
    ALERT_DANGER_TEMP = 38

    ALERT_SAFE = 0
    ALERT_WARNING = 1
    ALERT_DANGER = 2

    args = None

    def __init__(self, record_id, delay=2000):
        print('Init record_completer ...')

        #Use a config file
        conf = load_config()
        self.args = get_args()
        self.record_id = record_id
        self.DELAY = float(conf.get('CAPTURE_DELAY'))
        self.ALERT_WARNING_TEMP = float(conf.get('ALERT_WARNING_TEMP'))
        self.ALERT_DANGER_TEMP = float(conf.get('ALERT_DANGER_TEMP'))

        self.complete_record()

    def calculate_alert(self, temperature_body):
        alert = self.ALERT_SAFE
        if temperature_body > self.ALERT_DANGER_TEMP:
            alert = self.ALERT_DANGER
        elif temperature_body > self.ALERT_WARNING_TEMP:
            alert = self.ALERT_WARNING
        return alert

    def complete_record(self):
        camera = CameraThermal()

        end_time = datetime.now() + timedelta(milliseconds=self.DELAY)

        while True:
            frame = camera.get_frame()
            temperatures = frame.get('temperatures')
            if temperatures is None:
                # Restart timer
                end_time = datetime.now() + timedelta(milliseconds=self.DELAY)
            elif datetime.now() > end_time:

                # Take picture
                if self.args.simulator:
                    placeholder_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests/placeholder.jpg')
                    with open(placeholder_path, 'rb') as fh:
                        buf = BytesIO(fh.read())
                    image_rgb = buf.getvalue()
                else:
                    print("Take Picture!!--------")
                    image_rgb = camera_rgb.capture()

                db = sqlite3.connect(DATABASE)
                cur = db.cursor()

                cur.execute(
                    """UPDATE records SET t_timestamp = ?, t_temperature_mean = ?, t_temperature_median = ?, 
                    t_temperature_min = ?, t_temperature_max = ?, t_temperature_p10 = ?, t_temperature_p20 = ?, 
                    t_temperature_p30 = ?, t_temperature_p40 = ?, t_temperature_p50 = ?, t_temperature_p60 = ?, 
                    t_temperature_p70 = ?, t_temperature_p80 = ?, t_temperature_p90 = ?, t_temperature_body = ?,
                    t_image_thermal = ?, t_image_rgb = ?, t_alert = ? 
                    WHERE record_id = ?""",
                    (datetime.now().isoformat(), temperatures.get('temperature_mean'),
                     temperatures.get('temperature_median'), temperatures.get('temperature_min'),
                     temperatures.get('temperature_max'), temperatures.get('temperature_p10'),
                     temperatures.get('temperature_p20'), temperatures.get('temperature_p30'),
                     temperatures.get('temperature_p40'), temperatures.get('temperature_p50'),
                     temperatures.get('temperature_p60'), temperatures.get('temperature_p70'),
                     temperatures.get('temperature_p80'), temperatures.get('temperature_p90'),
                     temperatures.get('temperature_body'), frame.get('thermal_image'), image_rgb,
                     self.calculate_alert(temperatures.get('temperature_body')), self.record_id))
                db.commit()

                if self.args.cloud:
                    upload_record_by_id(self.record_id)
                break

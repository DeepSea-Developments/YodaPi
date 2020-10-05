import sys
import os

import sqlite3
import threading
import time
import requests
from base64 import b64encode
from scripts.database import DATABASE, dictfetchone, dictfetchall


def get_record(record_id):
    db = sqlite3.connect(DATABASE)
    cur = db.cursor()
    query = """SELECT * FROM records WHERE record_id=?"""
    cur.execute(query, (record_id,))
    data = dictfetchone(cur)

    image_thermal = data.get('t_image_thermal')
    if image_thermal is not None:
        data['t_image_thermal'] = b64encode(image_thermal).decode("utf-8")

    image_rgb = data.get('t_image_rgb')
    if image_rgb is not None:
        data['t_image_rgb'] = b64encode(image_rgb).decode("utf-8")

    return data


def upload_record(record_data):
    url = 'https://termodeep-prd-backend.azurewebsites.net/tenant/dsd/api/1.0/cameras/record/create/'
    # url = 'http://localhost:8040/tenant/dsd/api/1.0/cameras/record/create/'
    try:
        r = requests.post(url, record_data)
        if r.status_code == 201:
            db = sqlite3.connect(DATABASE)
            cur = db.cursor()
            query = """UPDATE records SET uploaded = 1 WHERE record_id = ?"""
            cur.execute(query, (record_data['record_id'],))
            db.commit()
    except Exception as e:
        print('Could not upload record ' + str(record_data['record_id']))


def upload_record_by_id(record_id):
    data = get_record(record_id)
    upload_record(data)


class CloudSynchronizer:
    thread = None

    # def __init__(self):

    def _thread(self):
        print('Starting cloud synchronizer.')
        db = sqlite3.connect(DATABASE)
        cur = db.cursor()

        # Check for pending records
        while True:
            cur.execute("""SELECT * FROM records WHERE uploaded=0 AND t_timestamp IS NOT NULL LIMIT 10""")
            data = dictfetchall(cur)
            for record in data:

                image_thermal = record.get('t_image_thermal')
                if image_thermal is not None:
                    record['t_image_thermal'] = b64encode(image_thermal).decode("utf-8")

                image_rgb = record.get('t_image_rgb')
                if image_rgb is not None:
                    record['t_image_rgb'] = b64encode(image_rgb).decode("utf-8")

                print('Uploading record ' + str(record['record_id']))
                upload_record(record)

            time.sleep(30)

    def start(self):
        """Start the background thread if it isn't running yet."""
        if self.thread is None:
            # start background thread
            self.thread = threading.Thread(target=self._thread)
            self.thread.start()

import requests

from scripts.helpers import load_config
from scripts.barcode_reader import BarcodeType
import base64

class ApiConnector:
    def __init__(self):
        self.door_id = 1
        self.conf = load_config()

        self.url = self.conf.get("api_url")
        self.token = self.conf.get("api_token")
        self.door_id = self.conf.get("door_id")

        self.headers = {'Accept': 'application/json',
                        'Authorization': self.token}

        # api endpoints
        self.api_get_users = self.conf.get('api_get_users')
        self.api_get_open_door_id = self.conf.get("api_get_open_door_id")
        self.api_get_open_door_qr = self.conf.get("api_get_open_door_qr")
        self.api_get_remote_open = self.conf.get("api_get_remote_open")
        self.api_post_close = self.conf.get("api_post_close")
        self.api_get_db_changes = self.conf.get("api_get_db_changes")

    def get_database(self):
        params = {'id_door': self.door_id}
        url = self.url + self.api_get_users.format(**params)
        print(url)
        r = requests.get(url,
                         headers=self.headers)
        return r

    def open_door(self, document, door_dir, barcode_type, qr_code=""):
        print(qr_code)
        base64_qr = base64.b64encode(qr_code.encode("ascii")).decode("utf-8")
        params = {'id_door': self.door_id,
                  'document': document,
                  'action': door_dir,
                  'qr_base64': base64_qr}
        if barcode_type == BarcodeType.QR.value:
            url = self.url + self.api_get_open_door_qr.format(**params)
        else:
            url = self.url + self.api_get_open_door_id.format(**params)
        print(url)
        r = requests.get(url,
                         headers=self.headers)
        return r

    def close_door(self):
        params = {'id_door': self.door_id}
        url = self.url + self.api_post_close.format(**params)
        print(url)
        r = requests.post(url,
                          headers=self.headers)
        return r

    def door_status_verification(self):
        try:
            params = {'id_door': self.door_id}
            url = self.url + self.api_get_remote_open.format(**params)
            print(url)
            r = requests.get(url,
                             headers=self.headers)
            return r
        except requests.exceptions.ConnectionError:
            raise requests.exceptions.ConnectionError
        except Exception as e:
            print("api.door_status_verification error: ", e)

    def get_last_db_change(self):
        try:
            params = {'id_door': self.door_id}
            url = self.url + self.api_get_db_changes.format(**params)
            print(url)
            r = requests.get(url,
                             headers=self.headers)
            return r
        except requests.exceptions.ConnectionError:
            raise requests.exceptions.ConnectionError
        except Exception as e:
            print("api.get_last_db_change error: ", e)
import requests

from scripts.helpers import load_config


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
        self.api_get_open_door = self.conf.get("api_get_open_door")
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

    def open_door(self, document, door_dir):
        params = {'id_door': self.door_id,
                  'document': document,
                  'action': door_dir}
        url = self.url + self.api_get_open_door.format(**params)
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
        params = {'id_door': self.door_id}
        url = self.url + self.api_get_remote_open.format(**params)
        print(url)
        r = requests.get(url,
                         headers=self.headers)
        return r

    def get_last_db_change(self):
        params = {'id_door': self.door_id}
        url = self.url + self.api_get_db_changes.format(**params)
        print(url)
        r = requests.get(url,
                         headers=self.headers)
        return r

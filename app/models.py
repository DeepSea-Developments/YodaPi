from sqlalchemy import Column, Integer, String, Float, LargeBinary, Boolean, DateTime, Enum, Date, Text

import scripts.db as db
import enum
from scripts.helpers import get_mac
from datetime import datetime


class BarcodeType(enum.Enum):
    national_id = 0,
    driving_id = 1,
    qr_code = 3


class EventType(enum.Enum):
    in_successful = 0,
    in_failed = 1,
    out_successful = 2,
    out_failed = 3,
    alarm_open_door = 4,
    door_open_manual = 5,
    door_open_remote = 6,
    door_close = 7


class AuthUser(db.Base):
    __tablename__ = 'AllowList'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    document = Column(Integer, nullable=False)
    access_key = Column(String)

    def __init__(self, name, document, access_key=None):
        self.name = name
        self.document = document
        self.access_key = access_key

    def __repr__(self):
        return f'User({self.name},{self.document})'

    def __str__(self):
        return self.name


class Event(db.Base):
    __tablename__ = 'records'
    record_id = Column(Integer, primary_key=True)
    mac_address = Column(String, nullable=False)
    uploaded = Column(Boolean)
    event_type = Column(Enum(EventType))
    timestamp = Column(DateTime)

    barcode_type = Column(Enum(BarcodeType))

    # National ID info
    name = Column(String)
    last_name = Column(String)
    document = Column(Integer)
    gender = Column(String)
    birth_date = Column(Date)
    blood_type = Column(String)

    # Extra data
    extra_json = Column(Text)
    extra_txt = Column(Text)
    rgb_photo = Column(LargeBinary)

    def __init__(self, event_type):
        self.mac_address = get_mac()
        self.uploaded = False
        self.event_type = event_type
        self.timestamp = datetime.now()

    def id(self, name, last_name, document, gender, birth_date, blood_type):
        self.name = name
        self.last_name = last_name
        self.document = document
        self.gender = gender
        self.birth_date = birth_date
        self.blood_type = blood_type

    def photo(self, photo):
        self.rgb_photo = photo

    # ToDo Fill other fields as extra_json or extra_txt

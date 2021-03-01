from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pathlib

Base = declarative_base()

DEFAULT_DATABASE_PATH = pathlib.Path(__file__).parent / '../data/yodapi_v1.db'

SessionLocal = None

def init(db_path=DEFAULT_DATABASE_PATH):
    global SessionLocal
    engine = create_engine(f'sqlite:///{db_path}',
                           echo=False,
                           connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(engine)

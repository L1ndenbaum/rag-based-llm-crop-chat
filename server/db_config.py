from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from os import getenv
from urllib.parse import quote_plus

DB_NAME = 'crop_chat_db'
DB_ADDR = 'localhost:3306'
DB_USERNAME = 'lindenbaum'
DB_PASSWORD = quote_plus(getenv('MySQLPassword', ""))
assert DB_NAME and DB_ADDR and DB_USERNAME and DB_PASSWORD, \
       "DB_NAME, DB_ADDR, DB_USERNAME, DB_PASSWORD 必须不为空"

SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_ADDR}/{DB_NAME}'
engine = create_engine(SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from flask_sqlalchemy import SQLAlchemy
import datetime, enum
from sqlalchemy import Enum
from datetime import datetime, timezone

db = SQLAlchemy()

class Users(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(255), nullable=False)
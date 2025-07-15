from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session

Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'
    username = Column(String(50), primary_key=True, index=True)
    password = Column(String(255), nullable=False)

# # 创建数据库表
# Base.metadata.create_all(bind=engine)


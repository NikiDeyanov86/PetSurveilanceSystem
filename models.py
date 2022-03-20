from sqlalchemy import Column, Integer, String, ForeignKey, DateTime,TIMESTAMP
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "User"

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(80), nullable=False)
    login_id = Column(String(36), nullable=True)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    @property
    def is_authenticated(self):
        return self.login_id != 0

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        False

    def get_id(self):
        return self.login_id


class Photo(Base):
    __tablename__ = 'Photo'

    id = Column(Integer, primary_key=True)
    location = Column(String(80), nullable=False)
    name = Column(String(80), unique=True, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now())

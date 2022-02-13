from sqlalchemy import Column, Integer, String
# from flask_login import UserMixin
from database import Base


class User(Base):
    __tablename__ = "User"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(50), nullable=False)
    # login_id = db.Column(db.String(36), nullable=True)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)


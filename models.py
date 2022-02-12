from app import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    __tablename__ = "User"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    # login_id = db.Column(db.String(36), nullable=True)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)


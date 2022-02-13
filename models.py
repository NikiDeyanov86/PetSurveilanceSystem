from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager


login = LoginManager()
db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "User"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(50), nullable=False)
    # login_id = db.Column(db.String(36), nullable=True)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

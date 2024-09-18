from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(255))
    websites = db.relationship('Website', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False)
    last_check = db.Column(db.DateTime, default=datetime.utcnow)
    last_change = db.Column(db.DateTime, nullable=True)
    last_content = db.Column(db.Text, nullable=True)
    check_interval = db.Column(db.Integer, default=24)  # in hours
    last_visited = db.Column(db.DateTime, nullable=True)
    is_reachable = db.Column(db.Boolean, default=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'last_change': self.last_change.isoformat() if self.last_change else None,
            'last_visited': self.last_visited.isoformat() if self.last_visited else None,
            'check_interval': self.check_interval,
            'is_reachable': self.is_reachable,
            'date_added': self.date_added.isoformat() if self.date_added else None,
        }

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(255))
    notification_email = db.Column(db.String(120), nullable=True)
    notifications_enabled = db.Column(db.Boolean, default=False, nullable=False)
    websites = db.relationship('Website', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    check_interval = db.Column(db.Integer, default=24)  # hours
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_reachable = db.Column(db.Boolean, default=True)
    last_check = db.Column(db.DateTime)  # When we last checked the site
    last_content = db.Column(db.Text)    # Content from last check
    last_change = db.Column(db.DateTime)  # When content last changed
    last_visited = db.Column(db.DateTime) # When user last visited
    date_added = db.Column(db.DateTime)   # When site was added

    @property
    def last_check_utc(self):
        """Ensure last_check is always UTC"""
        if self.last_check is None:
            return None
        return self.last_check if self.last_check.tzinfo else self.last_check.replace(tzinfo=timezone.utc)
    
    @property
    def last_change_utc(self):
        """Ensure last_change is always UTC"""
        if self.last_change is None:
            return None
        return self.last_change if self.last_change.tzinfo else self.last_change.replace(tzinfo=timezone.utc)
    
    @property
    def last_visited_utc(self):
        """Ensure last_visited is always UTC"""
        if self.last_visited is None:
            return None
        return self.last_visited if self.last_visited.tzinfo else self.last_visited.replace(tzinfo=timezone.utc)
    
    @property
    def date_added_utc(self):
        """Ensure date_added is always UTC"""
        if self.date_added is None:
            return None
        return self.date_added if self.date_added.tzinfo else self.date_added.replace(tzinfo=timezone.utc)

    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'last_check': self.last_check_utc.isoformat() + 'Z' if self.last_check_utc else None,
            'last_change': self.last_change_utc.isoformat() + 'Z' if self.last_change_utc else None,
            'last_content': self.last_content,
            'last_visited': self.last_visited_utc.isoformat() + 'Z' if self.last_visited_utc else None,
            'check_interval': self.check_interval,
            'is_reachable': self.is_reachable,
            'date_added': self.date_added_utc.isoformat() + 'Z' if self.date_added_utc else None,
        }

    @staticmethod
    def create(url, interval, user_id, current_time=None):
        """Centralized website creation logic"""
        if current_time is None:
            current_time = datetime.now(timezone.utc)
            
        website = Website(
            url=url,
            check_interval=interval,
            user_id=user_id,
            is_reachable=True,  # Default to true until checked
            last_check=None,    # No check yet
            last_content=None,  # No content yet
            last_visited=None,  # Not visited yet
            last_change=None,   # No changes yet
            date_added=current_time
        )
        return website

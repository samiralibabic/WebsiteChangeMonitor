from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), unique=True, nullable=False)
    last_check = db.Column(db.DateTime, default=datetime.utcnow)
    last_change = db.Column(db.DateTime, nullable=True)
    last_content = db.Column(db.Text, nullable=True)
    check_interval = db.Column(db.Integer, default=24)  # in hours
    last_visited = db.Column(db.DateTime, nullable=True)
    is_reachable = db.Column(db.Boolean, default=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

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

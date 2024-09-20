from urllib.request import urlopen
from urllib.error import URLError
from datetime import datetime
from models import db, Website
from datetime import datetime, timedelta

def check_website_changes():
    now = datetime.utcnow()
    websites = Website.query.filter(Website.last_check <= now - timedelta(minutes=Website.check_interval)).all()

    for website in websites:
        try:
            response = urlopen(website.url)
            new_content = response.read().decode('utf-8')
            if new_content != website.last_content:
                website.last_change = datetime.utcnow()
                website.last_content = new_content
            website.last_check = datetime.utcnow()
            website.is_reachable = True
        except URLError:
            website.is_reachable = False
        db.session.commit()
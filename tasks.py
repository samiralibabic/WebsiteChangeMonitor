from urllib.request import urlopen
from urllib.error import URLError
from datetime import datetime, timedelta
from models import db, Website
from flask import current_app
import logging

def check_website_changes(app):
    with app.app_context():
        logging.info("Starting check_website_changes function")
        now = datetime.utcnow()
        try:
            websites = Website.query.all()
            logging.info(f"Retrieved {len(websites)} websites")
        except Exception as e:
            logging.error(f"Error querying websites: {str(e)}")
            return

        for website in websites:
            logging.info(f"Checking website: {website.url}")
            if website.last_check is None or (now - website.last_check) >= timedelta(minutes=website.check_interval):
                try:
                    response = urlopen(website.url)
                    new_content = response.read().decode('utf-8')
                    if new_content != website.last_content:
                        website.last_change = now
                        website.last_content = new_content
                    website.is_reachable = True
                    logging.info(f"Successfully checked {website.url}")
                except URLError:
                    website.is_reachable = False
                    logging.warning(f"Failed to reach {website.url}")
                website.last_check = now
        try:
            db.session.commit()
            logging.info("Successfully committed changes to database")
        except Exception as e:
            logging.error(f"Error committing changes to database: {str(e)}")
        logging.info("Finished check_website_changes function")
from urllib.request import urlopen, Request
from urllib.error import URLError
from datetime import datetime, timedelta, timezone
from models import db, Website
from flask import current_app
import logging
from utils.email import send_unreachable_notification

logger = logging.getLogger(__name__)

def check_website_reachability(url, timeout=5):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        req = Request(url, headers=headers)
        response = urlopen(req, timeout=timeout)
        return True, response
    except Exception as e:
        logger.error(f"Error checking {url}: {str(e)}")
        return False, None

def get_website_content(response):
    try:
        content_type = response.headers.get('content-type', '').lower()
        if 'charset=' in content_type:
            encoding = content_type.split('charset=')[-1]
        else:
            encoding = 'utf-8'
        
        try:
            content = response.read().decode(encoding)
        except (UnicodeDecodeError, LookupError):
            try:
                content = response.read().decode('utf-8', errors='replace')
            except UnicodeDecodeError:
                content = f"Binary content (size: {len(response.read())} bytes)"
        return content
    except Exception as e:
        logger.error(f"Error getting content: {str(e)}")
        return None

def check_website_changes(website_ids):
    """Check websites for content changes"""
    current_time = datetime.now(timezone.utc)
    
    for website_id in website_ids:
        website = Website.query.get(website_id)
        if not website:
            continue
            
        logger.info(f"Checking website {website.url}")
        try:
            is_reachable, response = check_website_reachability(website.url)
            content = None
            
            if is_reachable and response:
                content = get_website_content(response)
                logger.info(f"Successfully checked {website.url}, content length: {len(content) if content else 0}")
                
                if website.last_content and content != website.last_content:
                    logger.info(f"Content changed for {website.url}")
                    website.last_change = current_time
            else:
                logger.warning(f"Website {website.url} is not reachable")
            
            website.is_reachable = is_reachable
            website.last_content = content
            website.last_check = current_time
            
            db.session.commit()
            logger.info(f"Updated database for {website.url}")
            
        except Exception as e:
            logger.error(f"Error checking website {website.url}: {str(e)}")

def schedule_periodic_checks(app):
    """Identify websites that need checking based on their intervals"""
    with app.app_context():
        logger.info("Checking for websites due for content check")  # More accurate description
        websites = Website.query.all()
        now = datetime.now(timezone.utc)
        
        for website in websites:
            if website.last_check is None:
                logger.info(f"Website {website.url} has never been checked, initiating first check")
                check_website_changes([website.id])
            else:
                last_check = website.last_check.replace(tzinfo=timezone.utc)
                time_since_check = now - last_check
                if time_since_check >= timedelta(hours=website.check_interval):
                    logger.info(
                        f"Website {website.url} is due for check: "
                        f"last check was {time_since_check} ago, "
                        f"check interval is {website.check_interval} hours"
                    )
                    check_website_changes([website.id])
                else:
                    logger.debug(
                        f"Website {website.url} not due for check yet: "
                        f"last check was {time_since_check} ago, "
                        f"check interval is {website.check_interval} hours"
                    )
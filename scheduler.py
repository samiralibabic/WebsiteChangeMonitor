from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from flask_apscheduler import APScheduler
import os

def init_scheduler(app):
    jobstores = {
        'default': SQLAlchemyJobStore(url=os.environ.get('DATABASE_URL'))
    }
    
    scheduler = APScheduler(BackgroundScheduler(jobstores=jobstores))
    scheduler.init_app(app)
    scheduler.start()
    
    return scheduler

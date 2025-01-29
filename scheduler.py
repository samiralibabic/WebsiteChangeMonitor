from apscheduler.schedulers.background import BackgroundScheduler
from tasks import schedule_periodic_checks

def init_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=lambda: schedule_periodic_checks(app),
        trigger='interval',
        minutes=1,  # Check every minute for websites that need updating
        id='website_scheduler',
        name='Schedule website checks'
    )
    scheduler.start()
    return scheduler

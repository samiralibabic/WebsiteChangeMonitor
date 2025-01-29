from flask_mail import Mail, Message
from flask import current_app

mail = Mail()

def send_unreachable_notification(user, website):
    if not user.notifications_enabled or not user.notification_email:
        return
        
    msg = Message(
        'Website Unreachable Alert',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.notification_email]
    )
    
    msg.body = f'''
    Hello {user.username},
    
    The website {website.url} is currently unreachable.
    Last successful check: {website.last_check}
    
    We'll notify you when the website becomes reachable again.
    
    Best regards,
    Website Change Monitor
    '''
    
    mail.send(msg) 
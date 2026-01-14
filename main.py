import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_cors import CORS
from models import db, User, Website
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from flask_migrate import Migrate
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo
from datetime import datetime, timezone
from sqlalchemy import text
from urllib.parse import urlparse
from dotenv import load_dotenv
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from scheduler import init_scheduler
from apscheduler.schedulers.background import BackgroundScheduler
from tasks import check_website_changes, schedule_periodic_checks
from email_validator import validate_email
from flask_mail import Mail

load_dotenv()

app = Flask(__name__)
CORS(app)

# Add datetime filter
def format_datetime(value):
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.rstrip('Z'))
        except ValueError:
            return value
    return value.strftime('%Y-%m-%d %H:%M:%S UTC')

app.jinja_env.filters['format_datetime'] = format_datetime

# Hard-coded SQLite database URI
basedir = os.path.abspath(os.path.dirname(__file__))
instance_dir = os.path.join(basedir, "instance")
os.makedirs(instance_dir, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_dir, "site.db")}'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')

# Set up logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy and Flask-Migrate
db.init_app(app)
migrate = Migrate(app, db)

# Mail configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# Initialize Flask-Mail
mail = Mail(app)

try:
    # Test the connection
    with app.app_context():
        db.engine.connect()
    app.logger.info("Database initialized successfully")
except Exception as e:
    app.logger.error(f"Error initializing database: {str(e)}")
    if 'SSL' in str(e):
        app.logger.error("SSL connection error. Please check your database SSL configuration.")
    exit(1)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_tables():
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Tables created successfully")
        except Exception as e:
            app.logger.error(f"Error creating tables: {str(e)}")
            exit(1)

def update_schema():
    with app.app_context():
        try:
            # Check if the column already exists with the correct type
            result = db.session.execute(text("PRAGMA table_info(user)")).fetchall()
            password_hash_column = next((col for col in result if col[1] == 'password_hash'), None)
            
            if password_hash_column is None or password_hash_column[2] != 'VARCHAR(255)':
                # If the column doesn't exist or has the wrong type, recreate the table
                db.session.execute(text('CREATE TABLE IF NOT EXISTS user_new (id INTEGER PRIMARY KEY AUTOINCREMENT, username VARCHAR(64) UNIQUE, password_hash VARCHAR(255))'))
                db.session.execute(text('INSERT OR IGNORE INTO user_new SELECT * FROM user'))
                db.session.execute(text('DROP TABLE IF EXISTS user'))
                db.session.execute(text('ALTER TABLE user_new RENAME TO user'))
                db.session.commit()
                app.logger.info("Database schema updated successfully")
            else:
                app.logger.info("Database schema is up to date")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating database schema: {str(e)}")
            exit(1)

class LoginForm(FlaskForm):
    class Meta:
        csrf = False
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    class Meta:
        csrf = False
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

@app.route('/')
def index():
    app.logger.debug(f"Index route accessed. User authenticated: {current_user.is_authenticated}")
    app.logger.debug(f"Current user: {current_user}")
    if current_user.is_authenticated:
        # Order by date_added descending (newest first)
        websites = Website.query.filter_by(user_id=current_user.id).order_by(Website.date_added.desc()).all()
        app.logger.debug(f"Found {len(websites)} websites for user {current_user.id}")
        return render_template('index.html', websites=websites)
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    session.pop('_flashes', None)
    app.logger.debug(f"Login route accessed. Method: {request.method}")
    if current_user.is_authenticated:
        app.logger.debug("User already authenticated, redirecting to index")
        return redirect(url_for('index'))
    
    form = LoginForm()
    app.logger.debug(f"Login form data: {request.form}")
    app.logger.debug(f"Form errors: {form.errors}")
    
    if form.validate_on_submit():
        app.logger.debug(f"Form validated. Attempting login for username: {form.username.data}")
        try:
            user = User.query.filter_by(username=form.username.data).first()
            app.logger.debug(f"User query result: {user}")
            if user is None or not user.check_password(form.password.data):
                app.logger.warning(f"Invalid username or password for: {form.username.data}")
                flash('Invalid username or password', 'error')
                return render_template('login.html', title='Sign In', form=form)
            
            login_user(user)
            app.logger.info(f"User {form.username.data} logged in successfully")
            flash('You have been logged in successfully!', 'success')
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('index')
            app.logger.debug(f"Redirecting to: {next_page}")
            return redirect(next_page)
        except Exception as e:
            app.logger.error(f"Error during login process: {str(e)}")
            flash('An error occurred during login. Please try again.', 'error')
            return render_template('login.html', title='Sign In', form=form)
    
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    session.pop('_flashes', None)
    logout_user()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    app.logger.info(f"Register route accessed. Method: {request.method}, Data: {request.form}")
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        app.logger.info(f"Form validated. Attempting to register user: {form.username.data}")
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            app.logger.warning(f"Username {form.username.data} already exists")
            flash('Username already exists. Please choose a different username.', 'error')
            return render_template('register.html', title='Register', form=form)
        try:
            user = User(username=form.username.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            app.logger.info(f"User {form.username.data} registered successfully")
            flash('Congratulations, you are now a registered user!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error registering user: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'error')
    else:
        app.logger.warning(f"Form validation failed: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}", 'error')
    return render_template('register.html', title='Register', form=form)

@app.route('/api/websites', methods=['GET'])
@login_required
def get_websites():
    websites = Website.query.filter_by(user_id=current_user.id).all()
    return jsonify([website.to_dict() for website in websites])

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
        try:
            response = urlopen(req, timeout=timeout)
            return True, response
        except HTTPError as he:
            # Both 304 (Not Modified) and 3xx (Redirects) are success cases
            if he.code == 304 or (300 <= he.code < 400):
                return True, he
            raise  # re-raise other HTTP errors
    except Exception as e:
        app.logger.error(f"Error checking {url}: {str(e)}")
        return False, None

@app.route('/api/websites', methods=['POST'])
@login_required
def add_website():
    data = request.json
    url = data['url']
    current_time = datetime.now(timezone.utc)

    # Check if URL already exists for this user
    existing_website = Website.query.filter_by(url=url, user_id=current_user.id).first()
    if existing_website:
        return jsonify({
            'error': 'URL already exists',
            'message': 'This website is already being monitored',
            'added': 0,
            'details': {
                'skipped': [{'url': url, 'reason': 'Already exists'}],
                'failed': []
            }
        }), 409

    try:
        new_website = Website.create(url, data['interval'], current_user.id, current_time)
        db.session.add(new_website)
        db.session.commit()

        # Queue for immediate check
        check_website_changes([new_website.id])

        return jsonify({
            'added': 1,
            'details': {
                'skipped': [],
                'failed': []
            },
            **new_website.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding website {url}: {str(e)}")
        return jsonify({
            'error': 'Failed to add website',
            'message': str(e),
            'added': 0,
            'details': {
                'skipped': [],
                'failed': [{'url': url, 'reason': str(e)}]
            }
        }), 500

@app.route('/api/websites/<int:id>', methods=['DELETE'])
@login_required
def remove_website(id):
    website = Website.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(website)
    db.session.commit()
    return '', 204

@app.route('/api/websites/<int:id>/interval', methods=['PATCH'])
@login_required
def update_interval(id):
    website = Website.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    
    if 'interval' not in data:
        return jsonify({'error': 'Missing interval parameter'}), 400
        
    interval = data['interval']
    
    # Validate interval
    if not isinstance(interval, (int, float)) or interval < 1 or interval > 24:
        return jsonify({'error': 'Invalid interval. Must be between 1 and 24 hours'}), 400
    
    website.check_interval = interval
    db.session.commit()
    
    return jsonify(website.to_dict())

@app.route('/api/websites/<int:id>/visit', methods=['POST'])
@login_required
def update_last_visited(id):
    website = Website.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    website.last_visited = datetime.now(timezone.utc)
    website.last_change = None  # Reset change detection when visiting
    db.session.commit()
    return jsonify(website.to_dict())

@app.route('/api/websites/bulk', methods=['POST'])
@login_required
def bulk_add_websites():
    data = request.json
    urls = data.get('urls', [])
    interval = data.get('interval', 24)
    current_time = datetime.now(timezone.utc)
    
    results = {
        'successful': [],
        'failed': [],
        'skipped': []
    }
    
    # Get existing URLs for this user to avoid duplicates
    existing_urls = set(
        website.url for website in 
        Website.query.filter_by(user_id=current_user.id).all()
    )
    
    # Batch process all URLs
    websites_to_add = []
    for url in urls:
        url = url.strip()
        if not url:
            continue
            
        if url in existing_urls:
            results['skipped'].append({
                'url': url,
                'reason': 'Already exists'
            })
            continue
        
        try:
            # Basic URL validation
            if not url.startswith(('http://', 'https://')):
                results['failed'].append({
                    'url': url,
                    'reason': 'Invalid URL format'
                })
                continue
                
            # Create website object - initially not checked
            website = Website.create(url, interval, current_user.id, current_time)
            websites_to_add.append(website)
            results['successful'].append(url)
            
        except Exception as e:
            results['failed'].append({
                'url': url,
                'reason': str(e)
            })
    
    try:
        if websites_to_add:
            db.session.bulk_save_objects(websites_to_add)
            db.session.commit()
            
            # Schedule immediate checks in background
            try:
                website_ids = [w.id for w in websites_to_add]
                check_website_changes(website_ids)
            except Exception as e:
                app.logger.error(f"Error scheduling checks: {str(e)}")
        
        return jsonify({
            'added': len(results['successful']),
            'skipped': len(results['skipped']),
            'failed': len(results['failed']),
            'details': results
        })
                
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in bulk add: {str(e)}")
        return jsonify({
            'error': 'Failed to add websites',
            'message': str(e)
        }), 500

@app.route('/api/user/notifications', methods=['POST'])
@login_required
def update_notification_settings():
    data = request.json
    email = data.get('email', '').strip()
    enabled = data.get('enabled', False)
    
    if enabled and not email:
        return jsonify({'error': 'Email required when notifications are enabled'}), 400
    
    if email and not validate_email(email):
        return jsonify({'error': 'Invalid email address'}), 400
    
    current_user.notification_email = email if enabled else None
    current_user.notifications_enabled = enabled
    db.session.commit()
    
    return jsonify({'message': 'Notification settings updated successfully'})

@app.route('/debug/websites')
@login_required
def debug_websites():
    websites = Website.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': w.id,
        'url': w.url,
        'check_interval': w.check_interval,
        'is_reachable': w.is_reachable,
        'user_id': w.user_id
    } for w in websites])

@app.route('/api/websites/all', methods=['DELETE'])
@login_required
def remove_all_websites():
    try:
        # Delete all websites for the current user
        Website.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error removing all websites: {str(e)}")
        return jsonify({
            'error': 'Failed to remove all websites',
            'message': str(e)
        }), 500

# Initialize tables and schema
with app.app_context():
    create_tables()
    update_schema()
    
# Initialize scheduler
scheduler = init_scheduler(app)

if __name__ == '__main__':
    app.logger.info("Starting Flask application on port 5001")
    app.run(host='0.0.0.0', port=5001, debug=True)

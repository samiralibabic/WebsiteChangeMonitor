import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from models import db, User, Website
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo
from datetime import datetime
from sqlalchemy import text
from urllib.parse import urlparse

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key')

# Set up logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url:
    app.logger.info("DATABASE_URL is set")
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url + '?sslmode=require'
else:
    app.logger.error("ERROR: DATABASE_URL is not set")
    exit(1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

try:
    db.init_app(app)
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
login_manager = LoginManager()
login_manager.init_app(app)
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
            db.session.execute(text('ALTER TABLE "user" ALTER COLUMN password_hash TYPE VARCHAR(255)'))
            db.session.commit()
            app.logger.info("Database schema updated successfully")
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
@login_required
def index():
    app.logger.debug(f"Index route accessed. User authenticated: {current_user.is_authenticated}")
    app.logger.debug(f"Current user: {current_user}")
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    app.logger.debug(f"Login route accessed. Method: {request.method}")
    if current_user.is_authenticated:
        app.logger.debug("User already authenticated, redirecting to index")
        return redirect(url_for('index'))
    
    form = LoginForm()
    app.logger.debug(f"Login form data: {request.form}")
    app.logger.debug(f"Form errors: {form.errors}")
    
    if request.method == 'POST':
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
                app.logger.debug(f"Next page: {next_page}")
                if not next_page or urlparse(next_page).netloc != '':
                    next_page = url_for('index')
                app.logger.debug(f"Redirecting to: {next_page}")
                return redirect(next_page)
            except Exception as e:
                app.logger.error(f"Error during login process: {str(e)}")
                flash('An error occurred during login. Please try again.', 'error')
        else:
            app.logger.warning(f"Form validation failed: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{field.capitalize()}: {error}", 'error')
    
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    app.logger.info(f"Register route accessed. Method: {request.method}, Data: {request.form}")
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if request.method == 'POST':
        app.logger.debug(f"POST request received. Form data: {request.form}")
        if form.validate_on_submit():
            app.logger.info(f"Form validated. Attempting to register user: {form.username.data}")
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                app.logger.warning(f"Username {form.username.data} already exists")
                return jsonify({'success': False, 'errors': {'username': 'Username already exists'}}), 400
            try:
                user = User(username=form.username.data)
                user.set_password(form.password.data)
                db.session.add(user)
                db.session.commit()
                app.logger.info(f"User {form.username.data} registered successfully")
                login_user(user)
                return jsonify({'success': True, 'redirect': url_for('index')})
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error registering user: {str(e)}")
                return jsonify({'success': False, 'errors': {'database': str(e)}}), 500
        else:
            app.logger.warning(f"Form validation failed: {form.errors}")
            return jsonify({'success': False, 'errors': form.errors}), 400
    return render_template('register.html', title='Register', form=form)

@app.route('/api/websites', methods=['GET'])
@login_required
def get_websites():
    websites = Website.query.filter_by(user_id=current_user.id).all()
    return jsonify([website.to_dict() for website in websites])

@app.route('/api/websites', methods=['POST'])
@login_required
def add_website():
    data = request.json
    new_website = Website(url=data['url'], check_interval=data['interval'], user_id=current_user.id)
    db.session.add(new_website)
    db.session.commit()
    return jsonify(new_website.to_dict()), 201

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
    data = request.json
    website.check_interval = data['interval']
    db.session.commit()
    return jsonify(website.to_dict())

@app.route('/api/websites/<int:id>/visit', methods=['POST'])
@login_required
def visit_website(id):
    website = Website.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    website.last_visited = datetime.utcnow()
    db.session.commit()
    return jsonify(website.to_dict())

@app.route('/debug/clear_users', methods=['POST'])
def clear_users():
    try:
        num_deleted = db.session.query(User).delete()
        db.session.commit()
        app.logger.info(f"Cleared {num_deleted} users from the database")
        return jsonify({"message": f"Successfully cleared {num_deleted} users from the database"}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error clearing users: {str(e)}")
        return jsonify({"error": "Failed to clear users from the database"}), 500

@app.route('/debug/auth_status')
def debug_auth_status():
    if current_user.is_authenticated:
        return jsonify({
            "is_authenticated": True,
            "user_id": current_user.id,
            "username": current_user.username
        }), 200
    else:
        return jsonify({"is_authenticated": False}), 200

if __name__ == '__main__':
    create_tables()
    update_schema()
    app.logger.info("Starting Flask application on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=True)

import os
from flask import Flask, render_template, request, jsonify
from models import db, Website
from scheduler import init_scheduler
from datetime import datetime
from bs4 import BeautifulSoup
import requests

app = Flask(__name__)

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url:
    print("DATABASE_URL is set")
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    print("ERROR: DATABASE_URL is not set")
    exit(1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

try:
    db.init_app(app)
    print("Database initialized successfully")
except Exception as e:
    print(f"Error initializing database: {str(e)}")
    exit(1)

# Initialize scheduler
scheduler = init_scheduler(app)

def create_tables():
    with app.app_context():
        try:
            # Drop the existing table
            Website.__table__.drop(db.engine, checkfirst=True)
            # Create the table with the updated schema
            db.create_all()
            print("Tables created successfully")
        except Exception as e:
            print(f"Error creating tables: {str(e)}")
            exit(1)

@app.route('/')
def index():
    return render_template('index.html')

def check_website_reachability(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error checking website {url}: {str(e)}")
        return False

@app.route('/api/websites', methods=['POST'])
def add_website():
    data = request.json
    url = data.get('url')
    interval = data.get('interval', 24)  # Default to 24 hours if not provided
    
    print(f"Received request to add website: {url} with interval: {interval}")
    
    try:
        existing_website = Website.query.filter_by(url=url).first()
        if existing_website:
            print(f"Website {url} already exists")
            return jsonify({'error': 'Website already exists'}), 400
        
        # Perform immediate check before adding to database
        is_reachable = check_website_reachability(url)
        
        current_time = datetime.utcnow()
        website = Website(url=url, check_interval=interval, last_visited=current_time, last_check=current_time, is_reachable=is_reachable, date_added=current_time)
        db.session.add(website)
        db.session.commit()
        
        print(f"Added website: {website.to_dict()}")
        
        # Schedule the recurring check
        scheduler.add_job(
            func=check_website,
            trigger='interval',
            hours=interval,
            id=f'check_{website.id}',
            args=[website.id]
        )
        
        return jsonify(website.to_dict()), 201
    except Exception as e:
        print(f"Error adding website: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/websites', methods=['GET'])
def get_websites():
    websites = Website.query.order_by(Website.date_added.desc()).all()
    return jsonify([website.to_dict() for website in websites])

@app.route('/api/websites/<int:website_id>', methods=['DELETE'])
def remove_website(website_id):
    website = Website.query.get_or_404(website_id)
    db.session.delete(website)
    db.session.commit()
    
    # Remove the scheduled job
    scheduler.remove_job(f'check_{website_id}')
    
    return '', 204

@app.route('/api/websites/<int:website_id>/visit', methods=['POST'])
def visit_website(website_id):
    website = Website.query.get_or_404(website_id)
    website.last_visited = datetime.utcnow()
    
    # Perform status check
    check_website(website_id)
    
    return jsonify(website.to_dict()), 200

@app.route('/api/websites/<int:website_id>/interval', methods=['PATCH'])
def update_interval(website_id):
    data = request.json
    new_interval = data.get('interval')
    
    website = Website.query.get_or_404(website_id)
    website.check_interval = new_interval
    db.session.commit()
    
    # Update the scheduled job
    scheduler.modify_job(
        id=f'check_{website_id}',
        func=check_website,
        trigger='interval',
        hours=new_interval,
        args=[website_id]
    )
    
    return jsonify(website.to_dict()), 200

def check_website(website_id):
    with app.app_context():
        website = Website.query.get(website_id)
        if not website:
            return
        
        print(f"Checking website: {website.url}")
        try:
            response = requests.get(website.url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            content = soup.get_text()
            
            if website.last_content is None:
                website.last_content = content
            elif content != website.last_content:
                website.last_content = content
                website.last_change = datetime.utcnow()
                print("Content changed, updating last_change")
            
            website.last_check = datetime.utcnow()
            website.is_reachable = True
            db.session.commit()
            print(f"Updated last_check: {website.last_check}")
        except Exception as e:
            print(f"Error checking website {website.url}: {str(e)}")
            website.is_reachable = False
            website.last_check = datetime.utcnow()
            db.session.commit()

if __name__ == '__main__':
    create_tables()
    print("Starting Flask application on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=True)

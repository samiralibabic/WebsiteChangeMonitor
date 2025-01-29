# Website Change Monitor

## Description

Website Change Monitor is a web application that allows users to track changes on specified websites. Users can add URLs to monitor, set check intervals, and receive visual notifications when changes are detected or when websites become unreachable.

## Features

- User authentication (login/register)
- Add websites to monitor
- Set custom check intervals for each website
- Visual status indicators for website changes and accessibility
- Email notifications for unreachable websites
- Responsive design for desktop and mobile use
- Automatic periodic checks of monitored websites
- Click-through to visit monitored websites

## Technologies Used

- Python 3.11+
- Flask (web framework)
- SQLAlchemy (ORM)
- APScheduler (for periodic tasks)
- BeautifulSoup4 (for parsing web content)
- HTML/CSS/JavaScript (frontend)
- SQLite (database)
- Gunicorn (WSGI server)
- Docker (containerization)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/website-change-monitor.git
   cd website-change-monitor
   ```

2. Create a `.env` file in the project root with the following variables:
   ```
   SECRET_KEY=your_secret_key
   DATABASE_URL=sqlite:///instance/site.db
   
   # Email configuration (optional)
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=your_app_password
   MAIL_DEFAULT_SENDER=your_email@gmail.com
   ```

3. Build and run with Docker:
   ```
   docker-compose up --build
   ```

The application will be available at `http://localhost:5002`

## Docker Setup

The application runs in a Docker container with the following configuration:

- Python 3.11 slim image
- Gunicorn as the WSGI server
- SQLite database persisted in a volume
- Automatic database migrations on startup

### Docker Commands

- Build and start: `docker-compose up --build`
- Start existing container: `docker-compose up -d`
- Stop container: `docker-compose down`
- View logs: `docker-compose logs -f`

## Project Structure

- `main.py`: Main application file
- `models.py`: Database models
- `tasks.py`: Tasks for periodic checks
- `scheduler.py`: Background task scheduler
- `templates/`: HTML templates
- `static/`: Static assets
  - `css/`: Stylesheets
  - `js/`: JavaScript files
- `migrations/`: Database migration files
- `instance/`: SQLite database location

## Usage

1. Register an account or log in
2. Add websites to monitor with their check intervals
3. The system will automatically check websites based on their intervals
4. Green status indicates changes since your last visit
5. Gray status means no changes or you've seen the latest changes
6. Red status indicates the website is unreachable
7. Configure email notifications in your user settings

## Development

For local development without Docker:

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables (see Installation section)

4. Initialize the database:
   ```
   flask db upgrade
   ```

5. Run the development server:
   ```
   python main.py
   ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Flask documentation and community
- SQLAlchemy documentation
- APScheduler documentation
- All contributors to the project

## Contact

For any queries or suggestions, please open an issue on the GitHub repository.
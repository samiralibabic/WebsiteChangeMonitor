# Website Change Monitor

## Description

Website Change Monitor is a web application that allows users to track changes on specified websites. Users can add URLs to monitor, set check intervals, and receive visual notifications when changes are detected or when websites become unreachable.

## Features

- User authentication (login/register)
- Add websites to monitor
- Set custom check intervals for each website
- Visual status indicators for website changes and accessibility
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
- PostgreSQL (database)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/website-change-monitor.git
   cd website-change-monitor
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows: `venv\Scripts\activate`
   - On macOS and Linux: `source venv/bin/activate`

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Set up environment variables:
   Create a `.env` file in the project root and add the following:
   ```
   SECRET_KEY=your_secret_key
   DATABASE_URL=postgresql://username:password@localhost/dbname
   ```

6. Initialize the database:
   ```
   flask db upgrade
   ```

7. Run the application:
   ```
   python app.py
   ```

## Project Structure

- `app.py`: Main application file
- `models.py`: Database models
- `forms.py`: Form definitions
- `templates/`: HTML templates
- `static/`: Static assets
  - `css/`: Stylesheets
  - `js/`: JavaScript files
- `migrations/`: Database migration files

## Usage

1. Register an account or log in
2. On the main page, enter a website URL and check interval (in hours)
3. Click "Add Website" to start monitoring
4. The website will appear in the list with its current status
5. Click on a website URL to visit it (this will also update its "last visited" time)
6. Use the "Update Interval" button to change the check frequency
7. Use the "Remove" button to stop monitoring a website

## Status Legend

- Green: Changes were made since the last time you visited
- Gray: No changes since your last visit, or you've already seen the changes
- Red: The website is unreachable or check is overdue

## Development

To contribute to the project:

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes and commit them
4. Push to your fork and submit a pull request

Please ensure your code adheres to the project's style guidelines.

## Deployment

This application can be deployed to various platforms that support Python web applications. Make sure to set the necessary environment variables and configure the database connection string for your production environment.

## Dependencies

Main dependencies include:

- Flask 3.0.3
- Flask-SQLAlchemy 3.1.1
- APScheduler 3.10.4
- Flask-APScheduler 1.13.1
- BeautifulSoup4 4.12.3
- Requests 2.32.3
- Flask-Login 0.6.3
- Flask-WTF 1.2.1
- SQLAlchemy 2.0.35
- Python-dotenv 1.0.0

For a full list of dependencies, refer to the `requirements.txt` file.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Flask documentation and community
- SQLAlchemy documentation
- APScheduler documentation
- All contributors to the project

## Contact

For any queries or suggestions, please open an issue on the GitHub repository.
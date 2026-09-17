# Student Management System

A browser-based student management system built with Python and Flask. I built it as a practical way to turn the original Tkinter version into a web application with a proper database-backed interface.

## What it does

- Admin login and session-based access
- Dashboard with student, teacher, subject and course counts
- Student records: create, search, edit and delete
- Automatically generated student IDs
- Cambridge-focused subject list and student enrolment
- Teacher records with subject assignment
- Attendance tracking by student and date
- Academic course/programme management
- School calendar and event management
- Light/dark theme
- Responsive interface for desktop and mobile screens

## Tech stack

- Python
- Flask
- SQLite
- Jinja templates
- HTML/CSS
- Gunicorn for deployment

## Run locally

1. Install Python 3.10+.
2. Clone this repository and open the project folder.
3. Install the dependencies:

```bash
pip install -r requirements.txt
```

4. Start the app:

```bash
python app.py
```

5. Open `http://127.0.0.1:5000` in your browser.

The app creates its local SQLite database automatically on first run. The database file is intentionally ignored by Git and is not included in this repository.

## Local authentication

A demo admin account is created automatically for local development. Its password is stored as a hash rather than plaintext in the application database.

For any real deployment, configure a proper administrator password and production authentication flow rather than relying on demo credentials.

## Configuration

Set a strong `FLASK_SECRET_KEY` environment variable before deploying. If it is not set during local development, the application generates a temporary secret for that process.

## Project notes

This is a learning/portfolio project rather than a production-ready school information system. Before using it with real student data, authentication and security should be strengthened further, including CSRF protection and a hosted database where appropriate.

## Deployment

The application can be run as a Python web service using Gunicorn:

```bash
gunicorn app:app
```

For a real deployment, environment-based configuration, HTTPS, CSRF protection and production database/security settings should be added before exposing the application publicly.

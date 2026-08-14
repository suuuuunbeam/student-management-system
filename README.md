# Student Management System — Web Version

This is the browser version of the Tkinter Student Management System.

## Features
- Admin login (`admin` / `admin123` for the demo)
- Dashboard
- Students CRUD
- Cambridge subjects and student enrolment
- Teachers CRUD
- Attendance
- Courses CRUD
- Calendar events CRUD
- Light/dark theme
- Settings page with account controls marked **UNDER CONSTRUCTION**
- Responsive layout for desktop and mobile browsers

## Run locally

1. Install Python.
2. Open a terminal in this folder.
3. Install the dependencies:

```bash
pip install -r requirements.txt
```

4. Start the website:

```bash
python app.py
```

5. Open `http://127.0.0.1:5000` in your browser.

## Deploy later

Push the folder to GitHub and deploy it as a Python web service. For Render, use:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`

Before public production use, replace the demo secret key, add proper password hashing, CSRF protection, and move from SQLite to a hosted database if multiple users will edit data at the same time.

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "students.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# Cambridge-focused subject list.
CAMBRIDGE_SUBJECTS = [
    ("English Language", "ENG"),
    ("English Literature", "LIT"),
    ("Mathematics", "MATH"),
    ("Additional Mathematics", "AMATH"),
    ("Physics", "PHY"),
    ("Chemistry", "CHEM"),
    ("Biology", "BIO"),
    ("Computer Science", "CS"),
    ("Economics", "ECO"),
    ("Business", "BUS"),
    ("Accounting", "ACC"),
    ("Geography", "GEO"),
    ("History", "HIST"),
    ("Global Perspectives", "GP"),
    ("Art & Design", "ART"),
    ("Environmental Management", "ENV"),
    ("Sociology", "SOC"),
    ("Psychology", "PSY"),
    ("Travel & Tourism", "TT"),
    ("Information Technology", "IT"),
    ("Physical Education", "PE"),
    ("Foreign Language", "LANG"),
]


def create_database():
    """Create the database and safely add columns needed by newer versions."""
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_code TEXT UNIQUE,
            name TEXT NOT NULL,
            dob TEXT,
            gender TEXT,
            class_name TEXT,
            section TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            guardian_name TEXT,
            guardian_phone TEXT,
            admission_year INTEGER,
            status TEXT DEFAULT 'Active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            code TEXT UNIQUE,
            level TEXT DEFAULT 'Cambridge',
            active INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_code TEXT UNIQUE,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            subject_id INTEGER,
            qualification TEXT,
            status TEXT DEFAULT 'Active',
            FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE SET NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            academic_year TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
            UNIQUE(student_id, subject_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            note TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
            UNIQUE(student_id, date)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT UNIQUE,
            name TEXT NOT NULL,
            level TEXT,
            description TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            event_date TEXT NOT NULL,
            event_type TEXT NOT NULL,
            description TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Simple local admin account for the app login.
    # For a real production app, store a hashed password instead.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            active INTEGER DEFAULT 1
        )
    """)
    cursor.execute(
        "INSERT OR IGNORE INTO users(username, password, role) VALUES (?, ?, ?)",
        ("admin", "admin123", "admin")
    )

    # Repair old databases created by earlier versions.
    existing = {
        row["name"] for row in cursor.execute("PRAGMA table_info(students)").fetchall()
    }
    required_columns = {
        "student_code": "TEXT",
        "dob": "TEXT",
        "gender": "TEXT",
        "class_name": "TEXT",
        "section": "TEXT",
        "phone": "TEXT",
        "email": "TEXT",
        "address": "TEXT",
        "guardian_name": "TEXT",
        "guardian_phone": "TEXT",
        "admission_year": "INTEGER",
        "status": "TEXT DEFAULT 'Active'",
        "created_at": "TEXT",
    }

    for column, definition in required_columns.items():
        if column not in existing:
            cursor.execute(
                f"ALTER TABLE students ADD COLUMN {column} {definition}")

    # Give old rows a generated code if they do not have one.
    old_rows = cursor.execute(
        "SELECT id, admission_year, class_name, student_code FROM students ORDER BY id"
    ).fetchall()
    for row in old_rows:
        if not row["student_code"]:
            year = row["admission_year"] or 2026
            class_code = class_to_code(row["class_name"] or "N/A")
            seq = row["id"]
            code = f"{year}-{class_code}-{seq:03d}"
            cursor.execute(
                "UPDATE students SET student_code=? WHERE id=?",
                (code, row["id"])
            )

    # Seed Cambridge subjects.
    for name, code in CAMBRIDGE_SUBJECTS:
        cursor.execute(
            "INSERT OR IGNORE INTO subjects(name, code, level) VALUES (?, ?, ?)",
            (name, code, "Cambridge")
        )

    # Helpful starter courses/programmes.
    starter_courses = [
        ("PRIMARY", "Cambridge Primary", "Primary", "Cambridge Primary programme"),
        ("LOWERSEC", "Cambridge Lower Secondary",
         "Lower Secondary", "Cambridge Lower Secondary programme"),
        ("IGCSE", "Cambridge IGCSE", "IGCSE", "Cambridge IGCSE programme"),
        ("AS", "Cambridge International AS Level",
         "AS Level", "Cambridge AS Level"),
        ("AL", "Cambridge International A Level", "A Level", "Cambridge A Level"),
    ]
    for code, name, level, description in starter_courses:
        cursor.execute(
            "INSERT OR IGNORE INTO courses(course_code, name, level, description) VALUES (?, ?, ?, ?)",
            (code, name, level, description)
        )

    cursor.execute(
        "INSERT OR IGNORE INTO settings(key, value) VALUES ('theme', 'light')"
    )

    connection.commit()
    connection.close()


def class_to_code(class_name):
    """Short code used in the student ID."""
    value = (class_name or "").strip().lower()

    mapping = {
        "playgroup": "PG",
        "nursery": "N",
        "kg": "KG",
        "kindergarten": "KG",
        "1": "01", "class 1": "01",
        "2": "02", "class 2": "02",
        "3": "03", "class 3": "03",
        "4": "04", "class 4": "04",
        "5": "05", "class 5": "05",
        "6": "06", "class 6": "06",
        "7": "07", "class 7": "07",
        "8": "08", "class 8": "08",
        "9": "09", "class 9": "09",
        "10": "10", "class 10": "10",
        "11": "11", "class 11": "11",
        "12": "12", "class 12": "12",
        "igcse": "IG",
        "as": "AS",
        "a level": "AL",
        "a-level": "AL",
    }
    return mapping.get(value, "00")


def generate_student_code(admission_year, class_name):
    connection = get_connection()
    prefix = f"{admission_year}-{class_to_code(class_name)}-"
    rows = connection.execute(
        "SELECT student_code FROM students WHERE student_code LIKE ?",
        (prefix + "%",)
    ).fetchall()
    connection.close()

    highest = 0
    for row in rows:
        code = row["student_code"] or ""
        try:
            highest = max(highest, int(code.split("-")[-1]))
        except (ValueError, IndexError):
            pass

    return f"{prefix}{highest + 1:03d}"


def save_student(data, student_id=None):
    connection = get_connection()
    cursor = connection.cursor()

    if student_id:
        cursor.execute("""
            UPDATE students SET
                name=?, dob=?, gender=?, class_name=?, section=?,
                phone=?, email=?, address=?, guardian_name=?,
                guardian_phone=?, admission_year=?, status=?
            WHERE id=?
        """, (
            data["name"], data["dob"], data["gender"], data["class_name"],
            data["section"], data["phone"], data["email"], data["address"],
            data["guardian_name"], data["guardian_phone"],
            data["admission_year"], data["status"], student_id
        ))
        connection.commit()
        connection.close()
        return cursor.execute(
            "SELECT * FROM students WHERE id=?", (student_id,)
        ).fetchone()

    code = generate_student_code(data["admission_year"], data["class_name"])

    cursor.execute("""
        INSERT INTO students(
            student_code, name, dob, gender, class_name, section,
            phone, email, address, guardian_name, guardian_phone,
            admission_year, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        code, data["name"], data["dob"], data["gender"], data["class_name"],
        data["section"], data["phone"], data["email"], data["address"],
        data["guardian_name"], data["guardian_phone"],
        data["admission_year"], data["status"]
    ))

    new_id = cursor.lastrowid
    connection.commit()
    row = cursor.execute(
        "SELECT * FROM students WHERE id=?", (new_id,)
    ).fetchone()
    connection.close()
    return row


def search_students(query):
    connection = get_connection()
    value = f"%{query.strip()}%"
    rows = connection.execute("""
        SELECT * FROM students
        WHERE student_code LIKE ? OR name LIKE ?
        ORDER BY name COLLATE NOCASE
    """, (value, value)).fetchall()
    connection.close()
    return rows


def get_student(student_id):
    connection = get_connection()
    row = connection.execute(
        "SELECT * FROM students WHERE id=?", (student_id,)
    ).fetchone()
    connection.close()
    return row


def get_student_by_code_or_name(value):
    connection = get_connection()
    value = value.strip()
    row = connection.execute("""
        SELECT * FROM students
        WHERE student_code = ? COLLATE NOCASE
           OR name = ? COLLATE NOCASE
        ORDER BY id
        LIMIT 1
    """, (value, value)).fetchone()
    connection.close()
    return row


def delete_student(student_id):
    connection = get_connection()
    connection.execute("DELETE FROM students WHERE id=?", (student_id,))
    connection.commit()
    connection.close()


def get_all_subjects():
    connection = get_connection()
    rows = connection.execute(
        "SELECT * FROM subjects WHERE active=1 ORDER BY name"
    ).fetchall()
    connection.close()
    return rows


def add_subject_to_student(student_id, subject_id, academic_year=""):
    connection = get_connection()
    try:
        connection.execute("""
            INSERT OR IGNORE INTO student_subjects(student_id, subject_id, academic_year)
            VALUES (?, ?, ?)
        """, (student_id, subject_id, academic_year))
        connection.commit()
    finally:
        connection.close()


def remove_subject_from_student(student_id, subject_id):
    connection = get_connection()
    connection.execute(
        "DELETE FROM student_subjects WHERE student_id=? AND subject_id=?",
        (student_id, subject_id)
    )
    connection.commit()
    connection.close()


def get_student_subjects(student_id):
    connection = get_connection()
    rows = connection.execute("""
        SELECT s.id, s.name, s.code, ss.academic_year
        FROM subjects s
        JOIN student_subjects ss ON ss.subject_id=s.id
        WHERE ss.student_id=?
        ORDER BY s.name
    """, (student_id,)).fetchall()
    connection.close()
    return rows


def get_subject_students(subject_id):
    connection = get_connection()
    rows = connection.execute("""
        SELECT st.*
        FROM students st
        JOIN student_subjects ss ON ss.student_id=st.id
        WHERE ss.subject_id=?
        ORDER BY st.name COLLATE NOCASE
    """, (subject_id,)).fetchall()
    connection.close()
    return rows


def save_teacher(data, teacher_id=None):
    connection = get_connection()
    cursor = connection.cursor()

    if teacher_id:
        cursor.execute("""
            UPDATE teachers SET name=?, phone=?, email=?, subject_id=?,
            qualification=?, status=? WHERE id=?
        """, (
            data["name"], data["phone"], data["email"], data["subject_id"],
            data["qualification"], data["status"], teacher_id
        ))
        connection.commit()
        row = cursor.execute(
            "SELECT * FROM teachers WHERE id=?", (teacher_id,)
        ).fetchone()
        connection.close()
        return row

    count = cursor.execute(
        "SELECT COUNT(*) AS n FROM teachers").fetchone()["n"] + 1
    code = f"T-{count:03d}"
    cursor.execute("""
        INSERT INTO teachers(
            teacher_code, name, phone, email, subject_id, qualification, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        code, data["name"], data["phone"], data["email"], data["subject_id"],
        data["qualification"], data["status"]
    ))
    connection.commit()
    row = cursor.execute(
        "SELECT * FROM teachers WHERE id=?", (cursor.lastrowid,)
    ).fetchone()
    connection.close()
    return row


def get_teachers():
    connection = get_connection()
    rows = connection.execute("""
        SELECT t.*, s.name AS subject_name, s.code AS subject_code
        FROM teachers t
        LEFT JOIN subjects s ON s.id=t.subject_id
        ORDER BY t.name COLLATE NOCASE
    """).fetchall()
    connection.close()
    return rows


def delete_teacher(teacher_id):
    connection = get_connection()
    connection.execute("DELETE FROM teachers WHERE id=?", (teacher_id,))
    connection.commit()
    connection.close()


def mark_attendance(student_id, date, status, note=""):
    connection = get_connection()
    connection.execute("""
        INSERT INTO attendance(student_id, date, status, note)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(student_id, date)
        DO UPDATE SET status=excluded.status, note=excluded.note
    """, (student_id, date, status, note))
    connection.commit()
    connection.close()


def get_attendance(date_value=None):
    connection = get_connection()
    if date_value:
        rows = connection.execute("""
            SELECT a.*, s.student_code, s.name, s.class_name
            FROM attendance a
            JOIN students s ON s.id=a.student_id
            WHERE a.date=?
            ORDER BY s.name COLLATE NOCASE
        """, (date_value,)).fetchall()
    else:
        rows = connection.execute("""
            SELECT a.*, s.student_code, s.name, s.class_name
            FROM attendance a
            JOIN students s ON s.id=a.student_id
            ORDER BY a.date DESC, s.name COLLATE NOCASE
        """).fetchall()
    connection.close()
    return rows


def get_student_attendance(student_id):
    connection = get_connection()
    rows = connection.execute("""
        SELECT * FROM attendance
        WHERE student_id=?
        ORDER BY date DESC
    """, (student_id,)).fetchall()
    connection.close()
    return rows


def save_course(data, course_id=None):
    connection = get_connection()
    cursor = connection.cursor()

    if course_id:
        cursor.execute("""
            UPDATE courses SET course_code=?, name=?, level=?, description=?
            WHERE id=?
        """, (
            data["course_code"], data["name"], data["level"],
            data["description"], course_id
        ))
    else:
        cursor.execute("""
            INSERT INTO courses(course_code, name, level, description)
            VALUES (?, ?, ?, ?)
        """, (
            data["course_code"], data["name"], data["level"],
            data["description"]
        ))

    connection.commit()
    connection.close()


def get_courses():
    connection = get_connection()
    rows = connection.execute(
        "SELECT * FROM courses ORDER BY name COLLATE NOCASE"
    ).fetchall()
    connection.close()
    return rows


def delete_course(course_id):
    connection = get_connection()
    connection.execute("DELETE FROM courses WHERE id=?", (course_id,))
    connection.commit()
    connection.close()


def save_event(data, event_id=None):
    connection = get_connection()
    cursor = connection.cursor()

    if event_id:
        cursor.execute("""
            UPDATE calendar_events SET title=?, event_date=?, event_type=?,
            description=? WHERE id=?
        """, (
            data["title"], data["event_date"], data["event_type"],
            data["description"], event_id
        ))
    else:
        cursor.execute("""
            INSERT INTO calendar_events(title, event_date, event_type, description)
            VALUES (?, ?, ?, ?)
        """, (
            data["title"], data["event_date"], data["event_type"],
            data["description"]
        ))

    connection.commit()
    connection.close()


def get_events():
    connection = get_connection()
    rows = connection.execute("""
        SELECT * FROM calendar_events
        ORDER BY event_date
    """).fetchall()
    connection.close()
    return rows


def delete_event(event_id):
    connection = get_connection()
    connection.execute("DELETE FROM calendar_events WHERE id=?", (event_id,))
    connection.commit()
    connection.close()


def get_counts():
    connection = get_connection()
    result = {
        "students": connection.execute(
            "SELECT COUNT(*) AS n FROM students WHERE status='Active'"
        ).fetchone()["n"],
        "teachers": connection.execute(
            "SELECT COUNT(*) AS n FROM teachers WHERE status='Active'"
        ).fetchone()["n"],
        "subjects": connection.execute(
            "SELECT COUNT(*) AS n FROM subjects WHERE active=1"
        ).fetchone()["n"],
        "courses": connection.execute(
            "SELECT COUNT(*) AS n FROM courses"
        ).fetchone()["n"],
    }
    connection.close()
    return result


def verify_user(username, password):
    """Return the user if the login details are correct."""
    connection = get_connection()
    row = connection.execute(
        "SELECT * FROM users WHERE username=? COLLATE NOCASE AND password=? AND active=1",
        (username.strip(), password)
    ).fetchone()
    connection.close()
    return row


def get_setting(key, default=""):
    connection = get_connection()
    row = connection.execute(
        "SELECT value FROM settings WHERE key=?", (key,)
    ).fetchone()
    connection.close()
    return row["value"] if row else default


def set_setting(key, value):
    connection = get_connection()
    connection.execute("""
        INSERT INTO settings(key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
    """, (key, value))
    connection.commit()
    connection.close()

from datetime import date
from functools import wraps
from flask import Flask, flash, redirect, render_template, request, session, url_for
import database

app = Flask(__name__)
app.secret_key = "change-this-demo-secret-before-production"
app.config["TEMPLATES_AUTO_RELOAD"] = True

database.create_database()

MENU = [
    ("dashboard", "Dashboard"),
    ("students", "Students"),
    ("subjects", "Subjects"),
    ("teachers", "Teachers"),
    ("attendance", "Attendance"),
    ("courses", "Courses"),
    ("calendar", "Calendar"),
    ("settings", "Settings"),
]


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_globals():
    return {
        "menu": MENU,
        "theme": database.get_setting("theme", "light"),
        "current_user": session.get("user"),
    }


@app.route("/", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = database.verify_user(username, password)
        if user:
            session["user"] = user["username"]
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", counts=database.get_counts())


@app.route("/students")
@login_required
def students():
    query = request.args.get("q", "")
    rows = database.search_students(query)
    return render_template("students.html", students=rows, query=query)


@app.route("/students/new", methods=["GET", "POST"])
@app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
def student_form(student_id=None):
    student = database.get_student(student_id) if student_id else None
    if request.method == "POST":
        try:
            year = int(request.form.get("admission_year", date.today().year))
        except ValueError:
            flash("Admission year must be a number.", "error")
            return render_template("student_form.html", student=student)

        data = {
            "name": request.form.get("name", "").strip(),
            "dob": request.form.get("dob", "").strip(),
            "gender": request.form.get("gender", "").strip(),
            "class_name": request.form.get("class_name", "").strip(),
            "section": request.form.get("section", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "email": request.form.get("email", "").strip(),
            "address": request.form.get("address", "").strip(),
            "guardian_name": request.form.get("guardian_name", "").strip(),
            "guardian_phone": request.form.get("guardian_phone", "").strip(),
            "admission_year": year,
            "status": request.form.get("status", "Active"),
        }
        if not data["name"] or not data["class_name"]:
            flash("Student name and class/level are required.", "error")
            return render_template("student_form.html", student=student)
        try:
            saved = database.save_student(data, student_id)
        except Exception as exc:
            flash(f"Could not save student: {exc}", "error")
            return render_template("student_form.html", student=student)
        if student_id:
            flash(f"{saved['name']} was updated.", "success")
        else:
            flash(f"Student saved. ID: {saved['student_code']}", "success")
        return redirect(url_for("students"))

    return render_template("student_form.html", student=student)


@app.post("/students/<int:student_id>/delete")
@login_required
def delete_student(student_id):
    database.delete_student(student_id)
    flash("Student deleted.", "success")
    return redirect(url_for("students"))


@app.route("/subjects")
@login_required
def subjects():
    subject_rows = database.get_all_subjects()
    selected_id = request.args.get("student_id", type=int)
    selected_student = database.get_student(
        selected_id) if selected_id else None
    enrolled = database.get_student_subjects(
        selected_id) if selected_id else []
    return render_template(
        "subjects.html",
        subjects=subject_rows,
        selected_student=selected_student,
        enrolled=enrolled,
        current_year=date.today().year,
    )


@app.post("/subjects/add")
@login_required
def add_subject():
    student_id = request.form.get("student_id", type=int)
    subject_id = request.form.get("subject_id", type=int)
    academic_year = request.form.get("academic_year", "").strip()
    if not student_id or not subject_id:
        flash("Select a student and a subject first.", "error")
    else:
        database.add_subject_to_student(student_id, subject_id, academic_year)
        flash("Subject added to student.", "success")
    return redirect(url_for("subjects", student_id=student_id))


@app.post("/subjects/remove")
@login_required
def remove_subject():
    student_id = request.form.get("student_id", type=int)
    subject_id = request.form.get("subject_id", type=int)
    if student_id and subject_id:
        database.remove_subject_from_student(student_id, subject_id)
        flash("Subject removed.", "success")
    return redirect(url_for("subjects", student_id=student_id))


@app.route("/teachers")
@login_required
def teachers():
    return render_template("teachers.html", teachers=database.get_teachers())


@app.route("/teachers/new", methods=["GET", "POST"])
@app.route("/teachers/<int:teacher_id>/edit", methods=["GET", "POST"])
@login_required
def teacher_form(teacher_id=None):
    teachers = database.get_teachers()
    teacher = next(
        (row for row in teachers if row["id"] == teacher_id), None) if teacher_id else None
    subjects = database.get_all_subjects()
    if request.method == "POST":
        subject_id = request.form.get("subject_id", type=int)
        data = {
            "name": request.form.get("name", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "email": request.form.get("email", "").strip(),
            "qualification": request.form.get("qualification", "").strip(),
            "status": request.form.get("status", "Active"),
            "subject_id": subject_id,
        }
        if not data["name"] or not subject_id:
            flash("Teacher name and subject are required.", "error")
            return render_template("teacher_form.html", teacher=teacher, subjects=subjects)
        try:
            database.save_teacher(data, teacher_id)
            flash("Teacher saved.", "success")
            return redirect(url_for("teachers"))
        except Exception as exc:
            flash(f"Could not save teacher: {exc}", "error")
    return render_template("teacher_form.html", teacher=teacher, subjects=subjects)


@app.post("/teachers/<int:teacher_id>/delete")
@login_required
def delete_teacher(teacher_id):
    database.delete_teacher(teacher_id)
    flash("Teacher deleted.", "success")
    return redirect(url_for("teachers"))


@app.route("/attendance")
@login_required
def attendance():
    selected_date = request.args.get("date", str(date.today()))
    return render_template("attendance.html", attendance=database.get_attendance(selected_date), selected_date=selected_date)


@app.post("/attendance")
@login_required
def save_attendance():
    student_value = request.form.get("student", "").strip()
    selected_date = request.form.get("date", str(date.today())).strip()
    row = database.get_student_by_code_or_name(student_value)
    if not row:
        matches = database.search_students(student_value)
        if len(matches) == 1:
            row = matches[0]
    if not row:
        flash("Student not found. Enter a student ID or exact name.", "error")
        return redirect(url_for("attendance", date=selected_date))
    database.mark_attendance(
        row["id"],
        selected_date,
        request.form.get("status", "Present"),
        request.form.get("note", "").strip(),
    )
    flash(f"Attendance saved for {row['name']}.", "success")
    return redirect(url_for("attendance", date=selected_date))


@app.route("/courses")
@login_required
def courses():
    return render_template("courses.html", courses=database.get_courses())


@app.route("/courses/new", methods=["GET", "POST"])
@app.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
@login_required
def course_form(course_id=None):
    course = next((row for row in database.get_courses()
                  if row["id"] == course_id), None) if course_id else None
    if request.method == "POST":
        data = {
            "course_code": request.form.get("course_code", "").strip(),
            "name": request.form.get("name", "").strip(),
            "level": request.form.get("level", "").strip(),
            "description": request.form.get("description", "").strip(),
        }
        if not data["course_code"] or not data["name"]:
            flash("Course code and name are required.", "error")
            return render_template("course_form.html", course=course)
        try:
            database.save_course(data, course_id)
            flash("Course saved.", "success")
            return redirect(url_for("courses"))
        except Exception as exc:
            flash(f"Could not save course: {exc}", "error")
    return render_template("course_form.html", course=course)


@app.post("/courses/<int:course_id>/delete")
@login_required
def delete_course(course_id):
    database.delete_course(course_id)
    flash("Course deleted.", "success")
    return redirect(url_for("courses"))


@app.route("/calendar")
@login_required
def calendar_page():
    return render_template("calendar.html", events=database.get_events())


@app.route("/calendar/new", methods=["GET", "POST"])
@app.route("/calendar/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
def event_form(event_id=None):
    event = next((row for row in database.get_events()
                 if row["id"] == event_id), None) if event_id else None
    if request.method == "POST":
        data = {
            "title": request.form.get("title", "").strip(),
            "event_date": request.form.get("event_date", "").strip(),
            "event_type": request.form.get("event_type", "General"),
            "description": request.form.get("description", "").strip(),
        }
        if not data["title"] or not data["event_date"]:
            flash("Event title and date are required.", "error")
            return render_template("event_form.html", event=event)
        try:
            database.save_event(data, event_id)
            flash("Event saved.", "success")
            return redirect(url_for("calendar_page"))
        except Exception as exc:
            flash(f"Could not save event: {exc}", "error")
    return render_template("event_form.html", event=event)


@app.post("/calendar/<int:event_id>/delete")
@login_required
def delete_event(event_id):
    database.delete_event(event_id)
    flash("Event deleted.", "success")
    return redirect(url_for("calendar_page"))


@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html", username=session.get("user", "admin"))


@app.post("/settings/theme")
@login_required
def set_theme():
    value = request.form.get("theme", "light")
    if value not in {"light", "dark"}:
        value = "light"
    database.set_setting("theme", value)
    return redirect(request.referrer or url_for("settings"))


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)

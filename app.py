import os
from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
import db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

db.init_db()


def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("projects"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if db.validate_user(request.form["username"], request.form["password"]):
            session["username"] = request.form["username"]
            return redirect(url_for("projects"))
        error = "Invalid username or password."
    return render_template("login.html", error=error)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        if db.create_user(request.form["username"], request.form["password"]):
            session["username"] = request.form["username"]
            return redirect(url_for("projects"))
        error = "Username already taken."
    return render_template("register.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Projects ──────────────────────────────────────────────────────────────────

@app.route("/projects")
@login_required
def projects():
    search    = request.args.get("search", "").strip().lower()
    has_bugs  = request.args.get("has_bugs", "")
    rows = db.get_projects(session["username"])
    if search:
        rows = [p for p in rows if search in p["name"].lower()
                or search in (p["description"] or "").lower()]
    if has_bugs == "yes":
        rows = [p for p in rows if p["open_bug_count"] > 0]
    elif has_bugs == "no":
        rows = [p for p in rows if p["open_bug_count"] == 0]
    return render_template("projects.html", projects=rows, search=search, has_bugs=has_bugs)


@app.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
def edit_project(project_id):
    project = db.get_project_by_id(project_id)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            return render_template("edit_project.html", project=project, error="Project name is required.")
        if db.project_name_exists(name, session["username"], exclude_id=project_id):
            return render_template("edit_project.html", project=project, error=f'A project named "{name}" already exists.')
        db.update_project(project_id, name, request.form.get("description", ""))
        return redirect(url_for("project_detail", project_id=project_id))
    return render_template("edit_project.html", project=project)


@app.route("/projects/<int:project_id>/delete", methods=["POST"])
@login_required
def delete_project(project_id):
    db.delete_project(project_id)
    return redirect(url_for("projects"))


@app.route("/projects/new", methods=["GET", "POST"])
@login_required
def new_project():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            return render_template("new_project.html", error="Project name is required.")
        if db.project_name_exists(name, session["username"]):
            return render_template("new_project.html", error=f'A project named "{name}" already exists.')
        db.create_project(name, request.form.get("description", ""), session["username"])
        return redirect(url_for("projects"))
    return render_template("new_project.html")


@app.route("/projects/<int:project_id>")
@login_required
def project_detail(project_id):
    project = db.get_project_by_id(project_id)
    files = db.get_project_files(project_id)
    sprint_numbers = db.get_sprint_numbers(project_id)
    search        = request.args.get("search", "").strip().lower()
    kind_filter   = request.args.get("kind", "")
    has_bugs      = request.args.get("has_bugs", "")
    sprint_filter = request.args.get("sprint", "")
    if search:
        files = [f for f in files if search in f["display_name"].lower()]
    if kind_filter:
        files = [f for f in files if f["file_kind"] == kind_filter]
    if has_bugs == "yes":
        files = [f for f in files if f["open_bug_count"] > 0]
    elif has_bugs == "no":
        files = [f for f in files if f["open_bug_count"] == 0]
    if sprint_filter:
        files = [f for f in files if str(f["sprint"] or "") == sprint_filter]
    return render_template("project.html", project=project, files=files,
                           search=search, kind_filter=kind_filter, has_bugs=has_bugs,
                           sprint_filter=sprint_filter, sprint_numbers=sprint_numbers,
                           file_kinds=db.FILE_KINDS)


# ── Project Files ─────────────────────────────────────────────────────────────

@app.route("/projects/<int:project_id>/files/new", methods=["GET", "POST"])
@login_required
def new_file(project_id):
    project = db.get_project_by_id(project_id)
    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        file_kind = request.form.get("file_kind", "").strip()
        sprint_raw = request.form.get("sprint", "").strip()
        sprint = None
        if sprint_raw:
            if not sprint_raw.isdigit() or int(sprint_raw) < 1:
                return render_template("new_file.html", project=project, file_kinds=db.FILE_KINDS,
                                       error="Sprint must be a positive integer.")
            sprint = int(sprint_raw)
        if not display_name or not file_kind:
            return render_template("new_file.html", project=project, file_kinds=db.FILE_KINDS,
                                   error="Name and Type are required.")
        if db.file_name_exists(project_id, display_name):
            return render_template("new_file.html", project=project, file_kinds=db.FILE_KINDS,
                                   error=f'An item named "{display_name}" already exists in this project.')
        db.create_project_file(project_id, display_name, file_kind, sprint)
        return redirect(url_for("project_detail", project_id=project_id))
    return render_template("new_file.html", project=project, file_kinds=db.FILE_KINDS)


@app.route("/projects/<int:project_id>/files/<int:file_id>/edit", methods=["GET", "POST"])
@login_required
def edit_file(project_id, file_id):
    project = db.get_project_by_id(project_id)
    file = db.get_project_file_by_id(file_id)
    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        file_kind = request.form.get("file_kind", "").strip()
        sprint_raw = request.form.get("sprint", "").strip()
        sprint = None
        if sprint_raw:
            if not sprint_raw.isdigit() or int(sprint_raw) < 1:
                return render_template("edit_file.html", project=project, file=file,
                                       file_kinds=db.FILE_KINDS, error="Sprint must be a positive integer.")
            sprint = int(sprint_raw)
        if not display_name or not file_kind:
            return render_template("edit_file.html", project=project, file=file,
                                   file_kinds=db.FILE_KINDS, error="Name and Type are required.")
        if db.file_name_exists(project_id, display_name, exclude_id=file_id):
            return render_template("edit_file.html", project=project, file=file,
                                   file_kinds=db.FILE_KINDS, error=f'An item named "{display_name}" already exists in this project.')
        db.update_project_file(file_id, display_name, file_kind, sprint)
        return redirect(url_for("project_detail", project_id=project_id))
    return render_template("edit_file.html", project=project, file=file, file_kinds=db.FILE_KINDS)


@app.route("/projects/<int:project_id>/files/<int:file_id>/delete", methods=["POST"])
@login_required
def delete_file(project_id, file_id):
    db.delete_project_file(file_id)
    return redirect(url_for("project_detail", project_id=project_id))


# ── Bug Reports ───────────────────────────────────────────────────────────────

@app.route("/projects/<int:project_id>/files/<int:file_id>/bugs")
@login_required
def bugs(project_id, file_id):
    project = db.get_project_by_id(project_id)
    files = db.get_project_files(project_id)
    current_file = next((f for f in files if f["id"] == file_id), None)
    search          = request.args.get("search", "").strip().lower()
    status_filter   = request.args.get("status", "")
    priority_filter = request.args.get("priority", "")
    rows = db.get_bug_reports(project_id=project_id, project_file_id=file_id)
    if search:
        rows = [b for b in rows if search in (b["title"] or "").lower()
                or search in (b["full_name"] or "").lower()
                or search in (b["description"] or "").lower()]
    if status_filter:
        rows = [b for b in rows if b["status"] == status_filter]
    if priority_filter:
        rows = [b for b in rows if b["priority"] == priority_filter]
    return render_template("bugs.html", project=project, file_id=file_id,
                           current_file=current_file, bugs=rows,
                           search=search, status_filter=status_filter,
                           priority_filter=priority_filter,
                           statuses=db.STATUSES, priorities=db.PRIORITIES)


@app.route("/projects/<int:project_id>/files/<int:file_id>/bugs/new", methods=["GET", "POST"])
@login_required
def new_bug(project_id, file_id):
    project = db.get_project_by_id(project_id)
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        title = request.form.get("title", "").strip()
        status = request.form.get("status", "").strip()
        found_date = request.form.get("found_date", "").strip()
        fixed_date = request.form.get("fixed_date", "").strip()
        if not full_name or not title or not status or not found_date:
            return render_template("new_bug.html", project=project, file_id=file_id,
                                   statuses=db.STATUSES, priorities=db.PRIORITIES,
                                   error="Reporter name, title, status, and found date are required.")
        if fixed_date and fixed_date < found_date:
            return render_template("new_bug.html", project=project, file_id=file_id,
                                   statuses=db.STATUSES, priorities=db.PRIORITIES,
                                   error="Fixed date must be on or after the found date.")
        if db.bug_title_exists(file_id, title):
            return render_template("new_bug.html", project=project, file_id=file_id,
                                   statuses=db.STATUSES, priorities=db.PRIORITIES,
                                   error=f'A bug titled "{title}" already exists in this item.')
        db.create_bug_report(
            project_id, file_id,
            full_name,
            status,
            found_date,
            fixed_date,
            request.form.get("priority", "Medium"),
            title,
            request.form.get("description", ""),
            request.form.get("progress_log", ""),
            request.form.get("additional_notes", ""),
        )
        return redirect(url_for("bugs", project_id=project_id, file_id=file_id))
    return render_template("new_bug.html", project=project, file_id=file_id,
                           statuses=db.STATUSES, priorities=db.PRIORITIES)


@app.route("/bugs/<int:bug_id>")
@login_required
def bug_detail(bug_id):
    bug = db.get_bug_report_by_id(bug_id)
    project = db.get_project_by_id(bug["project_id"])
    return render_template("bug_view.html", bug=bug, project=project)


@app.route("/bugs/<int:bug_id>/edit", methods=["GET", "POST"])
@login_required
def bug_edit(bug_id):
    bug = db.get_bug_report_by_id(bug_id)
    project = db.get_project_by_id(bug["project_id"])
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        title = request.form.get("title", "").strip()
        status = request.form.get("status", "").strip()
        found_date = request.form.get("found_date", "").strip()
        fixed_date = request.form.get("fixed_date", "").strip()
        if not full_name or not title or not status or not found_date:
            return render_template("bug.html", bug=bug, project=project,
                                   statuses=db.STATUSES, priorities=db.PRIORITIES,
                                   error="Reporter name, title, status, and found date are required.")
        if fixed_date and fixed_date < found_date:
            return render_template("bug.html", bug=bug, project=project,
                                   statuses=db.STATUSES, priorities=db.PRIORITIES,
                                   error="Fixed date must be on or after the found date.")
        if db.bug_title_exists(bug["project_file_id"], title, exclude_id=bug_id):
            return render_template("bug.html", bug=bug, project=project,
                                   statuses=db.STATUSES, priorities=db.PRIORITIES,
                                   error=f'A bug titled "{title}" already exists in this item.')
        db.update_bug_report(
            bug_id,
            full_name,
            status,
            found_date,
            fixed_date,
            request.form.get("priority", "Medium"),
            title,
            request.form.get("description", ""),
            request.form.get("progress_log", ""),
            request.form.get("additional_notes", ""),
        )
        return redirect(url_for("bug_detail", bug_id=bug_id))
    return render_template("bug.html", bug=bug, project=project,
                           statuses=db.STATUSES, priorities=db.PRIORITIES)


@app.route("/bugs/<int:bug_id>/delete", methods=["POST"])
@login_required
def delete_bug(bug_id):
    bug = db.get_bug_report_by_id(bug_id)
    project_id = bug["project_id"]
    file_id = bug["project_file_id"]
    db.delete_bug_report(bug_id)
    return redirect(url_for("bugs", project_id=project_id, file_id=file_id))


if __name__ == "__main__":
    db.drop_and_recreate()
    app.run(debug=True)

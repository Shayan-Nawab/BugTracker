import os
import hashlib
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

FILE_KINDS = [
    "Product Backlog Item",
    "Design Document",
    "Source Code",
    "Data File",
]

STATUSES   = ["Open", "In Progress", "Fixed", "Closed"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]


def get_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    owner TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS project_files (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    display_name TEXT NOT NULL,
                    file_kind TEXT,
                    sprint INTEGER,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """)
            cur.execute("""
                ALTER TABLE project_files ADD COLUMN IF NOT EXISTS sprint INTEGER
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS bug_reports (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    project_file_id INTEGER NOT NULL REFERENCES project_files(id) ON DELETE CASCADE,
                    full_name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Open',
                    found_date DATE,
                    fixed_date DATE,
                    priority TEXT NOT NULL DEFAULT 'Medium',
                    title TEXT,
                    description TEXT,
                    progress_log TEXT,
                    additional_notes TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """)
        conn.commit()
    finally:
        conn.close()


def drop_and_recreate():
    """Drop all tables and recreate. Destroys all data."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS bug_reports CASCADE")
            cur.execute("DROP TABLE IF EXISTS project_files CASCADE")
            cur.execute("DROP TABLE IF EXISTS projects CASCADE")
            cur.execute("DROP TABLE IF EXISTS users CASCADE")
        conn.commit()
    finally:
        conn.close()
    init_db()


# ── Auth ──────────────────────────────────────────────────────────────────────

def validate_user(username: str, password: str) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT password_hash FROM users WHERE username = %s", (username,)
            )
            row = cur.fetchone()
            return row is not None and row[0] == hash_password(password)
    finally:
        conn.close()


def create_user(username: str, password: str) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, hash_password(password)),
            )
        conn.commit()
        return True
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False
    finally:
        conn.close()


# ── Duplicate checks ──────────────────────────────────────────────────────────

def project_name_exists(name: str, owner: str, exclude_id: int = None) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if exclude_id:
                cur.execute(
                    "SELECT 1 FROM projects WHERE LOWER(name) = LOWER(%s) AND owner = %s AND id != %s",
                    (name, owner, exclude_id),
                )
            else:
                cur.execute(
                    "SELECT 1 FROM projects WHERE LOWER(name) = LOWER(%s) AND owner = %s",
                    (name, owner),
                )
            return cur.fetchone() is not None
    finally:
        conn.close()


def file_name_exists(project_id: int, display_name: str, exclude_id: int = None) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if exclude_id:
                cur.execute(
                    "SELECT 1 FROM project_files WHERE LOWER(display_name) = LOWER(%s) AND project_id = %s AND id != %s",
                    (display_name, project_id, exclude_id),
                )
            else:
                cur.execute(
                    "SELECT 1 FROM project_files WHERE LOWER(display_name) = LOWER(%s) AND project_id = %s",
                    (display_name, project_id),
                )
            return cur.fetchone() is not None
    finally:
        conn.close()


def bug_title_exists(project_file_id: int, title: str, exclude_id: int = None) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if exclude_id:
                cur.execute(
                    "SELECT 1 FROM bug_reports WHERE LOWER(title) = LOWER(%s) AND project_file_id = %s AND id != %s",
                    (title, project_file_id, exclude_id),
                )
            else:
                cur.execute(
                    "SELECT 1 FROM bug_reports WHERE LOWER(title) = LOWER(%s) AND project_file_id = %s",
                    (title, project_file_id),
                )
            return cur.fetchone() is not None
    finally:
        conn.close()


# ── Projects ──────────────────────────────────────────────────────────────────

def create_project(name: str, description: str, owner: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO projects (name, description, owner) VALUES (%s, %s, %s) RETURNING id",
                (name, description or None, owner),
            )
            project_id = cur.fetchone()[0]
        conn.commit()
        return project_id
    finally:
        conn.close()


def get_projects(owner: str):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT p.*,
                    COUNT(DISTINCT pf.id) AS file_count,
                    COUNT(DISTINCT b.id)  AS bug_count,
                    COUNT(DISTINCT b.id) FILTER (WHERE b.status NOT IN ('Fixed', 'Closed')) AS open_bug_count
                FROM projects p
                LEFT JOIN project_files pf ON pf.project_id = p.id
                LEFT JOIN bug_reports   b  ON b.project_id  = p.id
                WHERE p.owner = %s
                GROUP BY p.id
                ORDER BY p.updated_at DESC
                """,
                (owner,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_project_by_id(project_id: int):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
            return cur.fetchone()
    finally:
        conn.close()


def update_project(project_id: int, name: str, description: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE projects SET name = %s, description = %s, updated_at = NOW() WHERE id = %s",
                (name, description or None, project_id),
            )
        conn.commit()
    finally:
        conn.close()


def delete_project(project_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM projects WHERE id = %s", (project_id,))
        conn.commit()
    finally:
        conn.close()


# ── Project Files ─────────────────────────────────────────────────────────────

def create_project_file(project_id: int, display_name: str, file_kind: str, sprint: int = None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO project_files (project_id, display_name, file_kind, sprint) VALUES (%s, %s, %s, %s) RETURNING id",
                (project_id, display_name, file_kind or None, sprint),
            )
            file_id = cur.fetchone()[0]
        conn.commit()
        return file_id
    finally:
        conn.close()


def get_project_files(project_id: int):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT pf.*,
                    COUNT(b.id) AS bug_count,
                    COUNT(*) FILTER (WHERE b.status NOT IN ('Fixed', 'Closed')) AS open_bug_count
                FROM project_files pf
                LEFT JOIN bug_reports b ON b.project_file_id = pf.id
                WHERE pf.project_id = %s
                GROUP BY pf.id
                ORDER BY pf.updated_at DESC
                """,
                (project_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def update_project_file(file_id: int, display_name: str, file_kind: str, sprint: int = None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE project_files SET display_name = %s, file_kind = %s, sprint = %s, updated_at = NOW() WHERE id = %s",
                (display_name, file_kind or None, sprint, file_id),
            )
        conn.commit()
    finally:
        conn.close()


def get_sprint_numbers(project_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT sprint FROM project_files WHERE project_id = %s AND sprint IS NOT NULL ORDER BY sprint",
                (project_id,),
            )
            return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


def get_project_file_by_id(file_id: int):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM project_files WHERE id = %s", (file_id,))
            return cur.fetchone()
    finally:
        conn.close()


def delete_project_file(file_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM project_files WHERE id = %s", (file_id,))
        conn.commit()
    finally:
        conn.close()


# ── Bug Reports ───────────────────────────────────────────────────────────────

def create_bug_report(project_id: int, project_file_id: int, full_name: str,
                      status: str, found_date: str, fixed_date: str,
                      priority: str, title: str, description: str,
                      progress_log: str, additional_notes: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO bug_reports
                    (project_id, project_file_id, full_name, status, found_date,
                     fixed_date, priority, title, description, progress_log, additional_notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    project_id, project_file_id, full_name, status,
                    found_date or None, fixed_date or None,
                    priority, title or None, description or None,
                    progress_log or None, additional_notes or None,
                ),
            )
            bug_id = cur.fetchone()[0]
        conn.commit()
        return bug_id
    finally:
        conn.close()


def get_bug_reports(project_id=None, project_file_id=None):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            query = """
                SELECT b.*, pf.display_name AS file_name, p.name AS project_name
                FROM bug_reports b
                JOIN project_files pf ON pf.id = b.project_file_id
                JOIN projects      p  ON p.id  = b.project_id
                WHERE 1=1
            """
            params = []
            if project_id:
                query += " AND b.project_id = %s"
                params.append(project_id)
            if project_file_id:
                query += " AND b.project_file_id = %s"
                params.append(project_file_id)
            query += " ORDER BY b.updated_at DESC"
            cur.execute(query, params)
            return cur.fetchall()
    finally:
        conn.close()


def get_bug_report_by_id(bug_id: int):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM bug_reports WHERE id = %s", (bug_id,))
            return cur.fetchone()
    finally:
        conn.close()


def update_bug_report(bug_id: int, full_name: str, status: str, found_date: str,
                      fixed_date: str, priority: str, title: str,
                      description: str, progress_log: str, additional_notes: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE bug_reports SET
                    full_name        = %s,
                    status           = %s,
                    found_date       = %s,
                    fixed_date       = %s,
                    priority         = %s,
                    title         = %s,
                    description      = %s,
                    progress_log     = %s,
                    additional_notes = %s,
                    updated_at       = NOW()
                WHERE id = %s
                """,
                (
                    full_name, status,
                    found_date or None, fixed_date or None,
                    priority, title or None, description or None,
                    progress_log or None, additional_notes or None,
                    bug_id,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def delete_bug_report(bug_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM bug_reports WHERE id = %s", (bug_id,))
        conn.commit()
    finally:
        conn.close()

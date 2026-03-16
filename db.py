import os
import hashlib
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()


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
                    pseudo_path TEXT,
                    file_kind TEXT,
                    summary TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS bug_reports (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    project_file_id INTEGER NOT NULL REFERENCES project_files(id) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    description TEXT,
                    reporter TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Open',
                    priority TEXT NOT NULL DEFAULT 'Medium',
                    steps_to_reproduce TEXT,
                    expected_result TEXT,
                    actual_result TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """)
        conn.commit()
    finally:
        conn.close()


# ── Auth ──────────────────────────────────────────────────────────────────────

def validate_user(username: str, password: str) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT password_hash FROM users WHERE username = %s",
                (username,)
            )
            row = cur.fetchone()
            if row is None:
                return False
            return row[0] == hash_password(password)
    finally:
        conn.close()


def create_user(username: str, password: str) -> bool:
    """Returns False if username already exists."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, hash_password(password))
            )
        conn.commit()
        return True
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False
    finally:
        conn.close()


# ── Projects ──────────────────────────────────────────────────────────────────

def create_project(name: str, description: str, owner: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO projects (name, description, owner)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
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
                SELECT
                    p.*,
                    COUNT(DISTINCT pf.id) AS file_count,
                    COUNT(DISTINCT b.id) AS bug_count
                FROM projects p
                LEFT JOIN project_files pf ON pf.project_id = p.id
                LEFT JOIN bug_reports b ON b.project_id = p.id
                WHERE p.owner = %s
                GROUP BY p.id
                ORDER BY p.updated_at DESC, p.created_at DESC
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


# ── Project Files ─────────────────────────────────────────────────────────────

def create_project_file(project_id: int, display_name: str, pseudo_path: str,
                        file_kind: str, summary: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO project_files
                    (project_id, display_name, pseudo_path, file_kind, summary)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (project_id, display_name, pseudo_path or None, file_kind or None, summary or None),
            )
            project_file_id = cur.fetchone()[0]
        conn.commit()
        return project_file_id
    finally:
        conn.close()


def get_project_files(project_id: int):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    pf.*,
                    COUNT(b.id) AS bug_count,
                    COUNT(*) FILTER (WHERE b.status = 'Open') AS open_bug_count
                FROM project_files pf
                LEFT JOIN bug_reports b ON b.project_file_id = pf.id
                WHERE pf.project_id = %s
                GROUP BY pf.id
                ORDER BY pf.updated_at DESC, pf.created_at DESC
                """,
                (project_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


# ── Bug Reports ───────────────────────────────────────────────────────────────

def create_bug_report(project_id: int, project_file_id: int, title: str,
                      description: str, reporter: str, status: str, priority: str,
                      steps_to_reproduce: str, expected_result: str,
                      actual_result: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO bug_reports
                    (project_id, project_file_id, title, description, reporter,
                     status, priority, steps_to_reproduce, expected_result, actual_result)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    project_id,
                    project_file_id,
                    title,
                    description or None,
                    reporter,
                    status,
                    priority,
                    steps_to_reproduce or None,
                    expected_result or None,
                    actual_result or None,
                ),
            )
            bug_id = cur.fetchone()[0]
        conn.commit()
        return bug_id
    finally:
        conn.close()


def get_bug_reports(project_id=None, project_file_id=None,
                    status_filter=None, priority_filter=None, search_query=None):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            query = """
                SELECT
                    b.*,
                    pf.display_name AS file_name,
                    p.name AS project_name
                FROM bug_reports b
                JOIN project_files pf ON pf.id = b.project_file_id
                JOIN projects p ON p.id = b.project_id
                WHERE 1=1
            """
            params = []

            if project_id:
                query += " AND b.project_id = %s"
                params.append(project_id)

            if project_file_id:
                query += " AND b.project_file_id = %s"
                params.append(project_file_id)

            if status_filter and status_filter != "All":
                query += " AND b.status = %s"
                params.append(status_filter)

            if priority_filter and priority_filter != "All":
                query += " AND b.priority = %s"
                params.append(priority_filter)

            if search_query:
                like = f"%{search_query}%"
                query += """
                    AND (
                        b.title ILIKE %s
                        OR b.description ILIKE %s
                        OR b.reporter ILIKE %s
                        OR b.steps_to_reproduce ILIKE %s
                    )
                """
                params.extend([like, like, like, like])

            query += " ORDER BY b.updated_at DESC, b.created_at DESC"
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


def update_bug_report(bug_id: int, title: str, description: str, status: str,
                      priority: str, steps_to_reproduce: str,
                      expected_result: str, actual_result: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE bug_reports
                SET
                    title = %s,
                    description = %s,
                    status = %s,
                    priority = %s,
                    steps_to_reproduce = %s,
                    expected_result = %s,
                    actual_result = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (
                    title,
                    description or None,
                    status,
                    priority,
                    steps_to_reproduce or None,
                    expected_result or None,
                    actual_result or None,
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
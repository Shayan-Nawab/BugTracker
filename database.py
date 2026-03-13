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


# ── Bugs ──────────────────────────────────────────────────────────────────────

def get_all_bugs(status_filter=None, priority_filter=None, search_query=None):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            query = "SELECT * FROM bugs WHERE 1=1"
            params = []

            if status_filter and status_filter != "All":
                query += " AND status = %s"
                params.append(status_filter)

            if priority_filter and priority_filter != "All":
                query += " AND priority = %s"
                params.append(priority_filter)

            if search_query:
                query += " AND (title ILIKE %s OR description ILIKE %s OR reporter ILIKE %s OR category ILIKE %s)"
                like = f"%{search_query}%"
                params.extend([like, like, like, like])

            query += " ORDER BY created_at DESC"
            cur.execute(query, params)
            return cur.fetchall()
    finally:
        conn.close()


def get_bug_by_id(bug_id: int):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM bugs WHERE id = %s", (bug_id,))
            return cur.fetchone()
    finally:
        conn.close()


def create_bug(title, description, reporter, status, priority, category,
               artifact, found_date, fixed_date, notes):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO bugs
                    (title, description, reporter, status, priority, category,
                     artifact, found_date, fixed_date, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (title, description, reporter, status, priority, category,
                  artifact, found_date or None, fixed_date or None, notes))
            bug_id = cur.fetchone()[0]
        conn.commit()
        return bug_id
    finally:
        conn.close()


def update_bug(bug_id, title, description, status, priority, category,
               artifact, found_date, fixed_date, notes):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE bugs SET
                    title = %s, description = %s, status = %s, priority = %s,
                    category = %s, artifact = %s, found_date = %s,
                    fixed_date = %s, notes = %s, updated_at = NOW()
                WHERE id = %s
            """, (title, description, status, priority, category, artifact,
                  found_date or None, fixed_date or None, notes, bug_id))
        conn.commit()
    finally:
        conn.close()


def delete_bug(bug_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM bugs WHERE id = %s", (bug_id,))
        conn.commit()
    finally:
        conn.close()
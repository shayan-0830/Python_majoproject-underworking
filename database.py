"""Database layer: SQLite schema, password hashing and sample data."""
import hashlib
import secrets
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "quiz_system.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'student')),
    full_name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_option TEXT NOT NULL CHECK (correct_option IN ('A', 'B', 'C', 'D')),
    difficulty TEXT NOT NULL DEFAULT 'medium',
    marks INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS exams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    num_questions INTEGER NOT NULL,
    duration_minutes INTEGER NOT NULL,
    negative_marking REAL NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    exam_id INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    score REAL NOT NULL,
    total_marks INTEGER NOT NULL,
    correct INTEGER NOT NULL,
    wrong INTEGER NOT NULL,
    skipped INTEGER NOT NULL,
    time_taken_sec INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS attempt_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL,
    selected_option TEXT,
    is_correct INTEGER NOT NULL
);
"""

SAMPLE_QUESTIONS = [
    ("Which keyword defines a function in Python?", "func", "def", "define", "lambda", "B"),
    ("What is the output of len([1, 2, 3])?", "2", "3", "4", "Error", "B"),
    ("Which data type is immutable?", "list", "dict", "tuple", "set", "C"),
    ("Which symbol starts a single-line comment?", "//", "#", "/*", "--", "B"),
    ("What does pip do?", "Runs tests", "Installs packages", "Compiles code", "Formats code", "B"),
    ("What is the result of 3 ** 2?", "6", "9", "5", "1", "B"),
    ("Which method adds an item to the end of a list?", "add()", "insert_end()", "append()", "push()", "C"),
    ("Which keyword is used to handle exceptions?", "catch", "except", "rescue", "handle", "B"),
    ("What is type(5.0)?", "int", "float", "str", "double", "B"),
    ("Which module is used for SQLite in Python?", "sqlite3", "pysql", "dblite", "sqlx", "A"),
]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(8)
    digest = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${digest}"


def verify_password(password, stored):
    salt = stored.split("$", 1)[0]
    return secrets.compare_digest(hash_password(password, salt), stored)


def init_db():
    """Create tables, a default admin and some sample data on first run."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            conn.execute(
                "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, 'admin', ?)",
                ("admin", hash_password("admin123"), "Administrator"),
            )
        if conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0] == 0:
            cid = conn.execute("INSERT INTO categories (name) VALUES ('Python Basics')").lastrowid
            conn.executemany(
                "INSERT INTO questions (category_id, text, option_a, option_b, option_c, option_d, correct_option) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                [(cid,) + q for q in SAMPLE_QUESTIONS],
            )
            conn.execute(
                "INSERT INTO exams (title, category_id, num_questions, duration_minutes, negative_marking) "
                "VALUES ('Python Basics Quiz', ?, 10, 10, 0.25)",
                (cid,),
            )

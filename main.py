"""Quiz / Online Exam System - entry point.

Run:  python main.py
Default admin login:  admin / admin123
"""
import sqlite3

import admin
import exam_engine
import leaderboard
import results
from database import get_connection, hash_password, init_db, verify_password
from utils import ask, ask_password, header


def register():
    header("Student Registration")
    full_name = ask("Full name: ")
    username = ask("Choose a username: ").lower()
    password = ask_password("Choose a password (min 6 chars): ")
    if len(password) < 6:
        print("  Password too short.")
        return
    if password != ask_password("Confirm password: "):
        print("  Passwords do not match.")
        return
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, 'student', ?)",
                (username, hash_password(password), full_name),
            )
        print("  Registration successful. You can log in now.")
    except sqlite3.IntegrityError:
        print("  That username is already taken.")


def login():
    header("Login")
    username = ask("Username: ").lower()
    password = ask_password()
    with get_connection() as conn:
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if user and verify_password(password, user["password"]):
        return user
    print("  Invalid username or password.")
    return None


def student_menu(user):
    while True:
        header(f"Student Dashboard - {user['full_name']}")
        print("  1. Take an exam\n  2. My results\n  3. Leaderboard\n  4. Logout")
        choice = ask("Choice: ")
        if choice == "1":
            exam_engine.take_exam(user)
        elif choice == "2":
            results.student_history(user)
        elif choice == "3":
            leaderboard.show_leaderboard()
        elif choice == "4":
            return
        else:
            print("  Invalid choice.")


def main():
    init_db()
    while True:
        header("QUIZ / ONLINE EXAM SYSTEM")
        print("  1. Login\n  2. Register (student)\n  3. Exit")
        choice = ask("Choice: ")
        if choice == "1":
            user = login()
            if user:
                (admin.menu if user["role"] == "admin" else student_menu)(user)
        elif choice == "2":
            register()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("  Invalid choice.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting...")

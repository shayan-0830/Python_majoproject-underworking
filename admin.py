"""Admin panel: ties together question bank, exams, results, students, leaderboard."""
from database import get_connection
import exam_engine
import leaderboard
import question_bank
import results
from utils import ask, header, print_table


def list_students():
    header("Registered Students")
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT u.id, u.username, u.full_name, COUNT(a.id) AS attempts FROM users u "
            "LEFT JOIN attempts a ON a.user_id = u.id WHERE u.role = 'student' GROUP BY u.id ORDER BY u.id"
        ).fetchall()
    print_table(["ID", "Username", "Name", "Attempts"],
                [(r["id"], r["username"], r["full_name"], r["attempts"]) for r in rows])


def menu(user):
    while True:
        header(f"Admin Panel - {user['full_name']}")
        print("  1. Question bank\n  2. Manage exams\n  3. View all results\n  4. Leaderboard\n"
              "  5. View students\n  6. Export results to CSV\n  7. Logout")
        choice = ask("Choice: ")
        if choice == "1":
            question_bank.menu()
        elif choice == "2":
            exam_engine.menu()
        elif choice == "3":
            results.all_results_ui()
        elif choice == "4":
            leaderboard.show_leaderboard()
        elif choice == "5":
            list_students()
        elif choice == "6":
            results.export_all_csv()
        elif choice == "7":
            return
        else:
            print("  Invalid choice.")

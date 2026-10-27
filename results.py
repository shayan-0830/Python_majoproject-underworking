"""Result generation: on-screen report, answer review, history, exports."""
import csv
from pathlib import Path

from database import get_connection
from utils import ask, ask_int, fmt_time, header, print_table

PASS_PERCENT = 40
REPORT_DIR = Path(__file__).resolve().parent / "reports"


def _attempt(attempt_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT a.*, e.title, u.full_name, u.username FROM attempts a "
            "JOIN exams e ON e.id = a.exam_id JOIN users u ON u.id = a.user_id WHERE a.id = ?",
            (attempt_id,),
        ).fetchone()


def _review_rows(attempt_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT q.text, q.correct_option, aa.selected_option, aa.is_correct FROM attempt_answers aa "
            "JOIN questions q ON q.id = aa.question_id WHERE aa.attempt_id = ? ORDER BY aa.id",
            (attempt_id,),
        ).fetchall()


def build_report(attempt_id):
    a = _attempt(attempt_id)
    pct = (a["score"] / a["total_marks"] * 100) if a["total_marks"] else 0
    lines = [
        "RESULT REPORT",
        "-" * 40,
        f"Student   : {a['full_name']} ({a['username']})",
        f"Exam      : {a['title']}",
        f"Date      : {a['submitted_at']} (UTC)",
        f"Score     : {a['score']} / {a['total_marks']}  ({pct:.1f}%)",
        f"Correct   : {a['correct']}   Wrong: {a['wrong']}   Skipped: {a['skipped']}",
        f"Time taken: {fmt_time(a['time_taken_sec'])}",
        f"Result    : {'PASS' if pct >= PASS_PERCENT else 'FAIL'} (pass mark {PASS_PERCENT}%)",
        "",
        "ANSWER REVIEW",
        "-" * 40,
    ]
    for i, r in enumerate(_review_rows(attempt_id), 1):
        mark = "Correct" if r["is_correct"] else ("Skipped" if r["selected_option"] is None else "Wrong")
        lines.append(f"Q{i}. {r['text']}")
        lines.append(f"     Your answer: {r['selected_option'] or '-'} | Correct: {r['correct_option']} | {mark}")
    return "\n".join(lines)


def export_report(attempt_id):
    REPORT_DIR.mkdir(exist_ok=True)
    path = REPORT_DIR / f"result_attempt_{attempt_id}.txt"
    path.write_text(build_report(attempt_id), encoding="utf-8")
    return path


def show_result(attempt_id):
    header("Your Result")
    print(build_report(attempt_id))
    path = export_report(attempt_id)
    print(f"\n  Report saved to: {path}")


def student_history(user):
    header("My Results")
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT a.id, e.title, a.score, a.total_marks, a.time_taken_sec, a.submitted_at FROM attempts a "
            "JOIN exams e ON e.id = a.exam_id WHERE a.user_id = ? ORDER BY a.id DESC", (user["id"],)
        ).fetchall()
    print_table(
        ["Attempt", "Exam", "Score", "Time", "Date (UTC)"],
        [(r["id"], r["title"], f"{r['score']}/{r['total_marks']}", fmt_time(r["time_taken_sec"]), r["submitted_at"])
         for r in rows],
    )
    if rows:
        aid = ask_int("Attempt ID to view full report (0 to go back): ", 0)
        if aid in {r["id"] for r in rows}:
            print("\n" + build_report(aid))


def all_results_ui():
    header("All Results")
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT a.id, u.username, e.title, a.score, a.total_marks, a.time_taken_sec, a.submitted_at "
            "FROM attempts a JOIN users u ON u.id = a.user_id JOIN exams e ON e.id = a.exam_id ORDER BY a.id DESC"
        ).fetchall()
    print_table(
        ["Attempt", "Student", "Exam", "Score", "Time", "Date (UTC)"],
        [(r["id"], r["username"], r["title"], f"{r['score']}/{r['total_marks']}",
          fmt_time(r["time_taken_sec"]), r["submitted_at"]) for r in rows],
    )
    if rows:
        aid = ask_int("Attempt ID to view full report (0 to go back): ", 0)
        if aid in {r["id"] for r in rows}:
            print("\n" + build_report(aid))


def export_all_csv():
    REPORT_DIR.mkdir(exist_ok=True)
    path = REPORT_DIR / "all_results.csv"
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT a.id, u.username, u.full_name, e.title, a.score, a.total_marks, a.correct, a.wrong, "
            "a.skipped, a.time_taken_sec, a.submitted_at FROM attempts a JOIN users u ON u.id = a.user_id "
            "JOIN exams e ON e.id = a.exam_id ORDER BY a.id"
        ).fetchall()
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["attempt_id", "username", "full_name", "exam", "score", "total_marks",
                    "correct", "wrong", "skipped", "time_taken_sec", "submitted_at"])
        w.writerows([tuple(r) for r in rows])
    print(f"  Exported {len(rows)} result(s) to {path}")

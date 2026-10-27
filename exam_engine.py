"""Test engine: exam setup, timed exam session, scoring."""
import time

from database import get_connection
import question_bank
import results
from utils import ask_float, ask_int, ask, confirm, fmt_time, header, print_table


# ---------- exam management ----------
def list_exams(active_only=False):
    sql = ("SELECT e.*, c.name AS category FROM exams e JOIN categories c ON c.id = e.category_id")
    if active_only:
        sql += " WHERE e.is_active = 1"
    with get_connection() as conn:
        return conn.execute(sql + " ORDER BY e.id").fetchall()


def create_exam(title, category_id, num_questions, duration_minutes, negative_marking):
    with get_connection() as conn:
        return conn.execute(
            "INSERT INTO exams (title, category_id, num_questions, duration_minutes, negative_marking) "
            "VALUES (?, ?, ?, ?, ?)",
            (title, category_id, num_questions, duration_minutes, negative_marking),
        ).lastrowid


def set_exam_active(exam_id, active):
    with get_connection() as conn:
        return conn.execute("UPDATE exams SET is_active = ? WHERE id = ?", (int(active), exam_id)).rowcount


def delete_exam(exam_id):
    with get_connection() as conn:
        return conn.execute("DELETE FROM exams WHERE id = ?", (exam_id,)).rowcount


def show_exams(exams):
    print_table(
        ["ID", "Title", "Category", "Questions", "Minutes", "Neg.", "Status"],
        [(e["id"], e["title"], e["category"], e["num_questions"], e["duration_minutes"],
          e["negative_marking"], "Active" if e["is_active"] else "Hidden") for e in exams],
    )


# ---------- exam session ----------
def run_exam(user, exam):
    questions = question_bank.random_questions(exam["category_id"], exam["num_questions"])
    if not questions:
        print("  This exam has no questions yet. Ask the admin to add some.")
        return None

    total_marks = sum(q["marks"] for q in questions)
    duration = exam["duration_minutes"] * 60
    header(exam["title"])
    print(f"  Questions : {len(questions)}   Total marks: {total_marks}")
    print(f"  Time limit: {exam['duration_minutes']} minute(s)")
    print(f"  Negative marking: {exam['negative_marking']} x marks per wrong answer")
    print("  Answer with A/B/C/D, or S to skip. The clock runs across the whole test.")
    input("\n  Press Enter to start...")

    start = time.time()
    deadline = start + duration
    answers = {}
    timed_out = False

    for i, q in enumerate(questions, 1):
        remaining = deadline - time.time()
        if remaining <= 0:
            timed_out = True
            break
        print(f"\n--- Q{i}/{len(questions)}  [{q['marks']} mark(s)]  Time left: {fmt_time(remaining)} ---")
        print(q["text"])
        for letter in "ABCD":
            print(f"   {letter}. {q['option_' + letter.lower()]}")
        while True:
            ans = input("Your answer (A/B/C/D, S=skip): ").strip().upper()
            if ans in ("A", "B", "C", "D", "S"):
                break
            print("  Invalid input.")
        if time.time() > deadline:
            print("\n  Time is up! That last answer was not counted.")
            timed_out = True
            break
        answers[q["id"]] = None if ans == "S" else ans

    end = time.time()
    if timed_out:
        print("\n  Test auto-submitted because time expired.")
    return _save_attempt(user, exam, questions, answers, total_marks, min(int(end - start), duration))


def _save_attempt(user, exam, questions, answers, total_marks, time_taken):
    score, correct, wrong, skipped = 0.0, 0, 0, 0
    graded = []
    for q in questions:
        selected = answers.get(q["id"])
        if selected is None:
            skipped += 1
            graded.append((q["id"], None, 0))
        elif selected == q["correct_option"]:
            correct += 1
            score += q["marks"]
            graded.append((q["id"], selected, 1))
        else:
            wrong += 1
            score -= exam["negative_marking"] * q["marks"]
            graded.append((q["id"], selected, 0))
    score = max(round(score, 2), 0)

    with get_connection() as conn:
        attempt_id = conn.execute(
            "INSERT INTO attempts (user_id, exam_id, score, total_marks, correct, wrong, skipped, time_taken_sec) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user["id"], exam["id"], score, total_marks, correct, wrong, skipped, time_taken),
        ).lastrowid
        conn.executemany(
            "INSERT INTO attempt_answers (attempt_id, question_id, selected_option, is_correct) VALUES (?, ?, ?, ?)",
            [(attempt_id,) + g for g in graded],
        )
    return attempt_id


def take_exam(user):
    header("Available Exams")
    exams = list_exams(active_only=True)
    if not exams:
        print("  No exams available right now.")
        return
    show_exams(exams)
    valid = {e["id"]: e for e in exams}
    exam_id = ask_int("Exam ID to attempt (0 to cancel): ", 0)
    if exam_id == 0:
        return
    if exam_id not in valid:
        print("  Invalid exam ID.")
        return
    attempt_id = run_exam(user, valid[exam_id])
    if attempt_id:
        results.show_result(attempt_id)


# ---------- admin UI ----------
def _create_exam_ui():
    header("Create Exam")
    cid = question_bank.pick_category(allow_new=False)
    title = ask("Exam title: ")
    n = ask_int("Number of questions: ", 1, 200)
    minutes = ask_int("Duration (minutes): ", 1, 300)
    neg = ask_float("Negative marking per wrong answer (0 - 1, as fraction of marks): ", 0, 1)
    create_exam(title, cid, n, minutes, neg)
    print("  Exam created.")


def menu():
    while True:
        header("Manage Exams")
        print("  1. Create exam\n  2. View exams\n  3. Show/Hide exam\n  4. Delete exam\n  5. Back")
        choice = ask("Choice: ")
        if choice == "1":
            _create_exam_ui()
        elif choice == "2":
            show_exams(list_exams())
        elif choice == "3":
            show_exams(list_exams())
            eid = ask_int("Exam ID (0 to cancel): ", 0)
            if eid:
                exam = next((e for e in list_exams() if e["id"] == eid), None)
                if exam:
                    set_exam_active(eid, not exam["is_active"])
                    print("  Updated.")
                else:
                    print("  No such exam.")
        elif choice == "4":
            show_exams(list_exams())
            eid = ask_int("Exam ID to delete (0 to cancel): ", 0)
            if eid and confirm("This also deletes all results for this exam. Continue?"):
                print("  Deleted." if delete_exam(eid) else "  No such exam.")
        elif choice == "5":
            return
        else:
            print("  Invalid choice.")

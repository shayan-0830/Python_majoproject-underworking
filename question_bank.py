"""Question bank module: categories, questions, CSV import, random selection."""
import csv
from pathlib import Path

from database import get_connection
from utils import ask, ask_int, confirm, header, print_table


# ---------- data functions ----------
def get_categories():
    with get_connection() as conn:
        return conn.execute(
            "SELECT c.id, c.name, COUNT(q.id) AS total FROM categories c "
            "LEFT JOIN questions q ON q.category_id = c.id GROUP BY c.id ORDER BY c.id"
        ).fetchall()


def get_or_create_category(name):
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM categories WHERE name = ? COLLATE NOCASE", (name,)).fetchone()
        if row:
            return row["id"]
        return conn.execute("INSERT INTO categories (name) VALUES (?)", (name,)).lastrowid


def add_question(category_id, text, options, correct, difficulty="medium", marks=1):
    with get_connection() as conn:
        return conn.execute(
            "INSERT INTO questions (category_id, text, option_a, option_b, option_c, option_d, "
            "correct_option, difficulty, marks) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (category_id, text, *options, correct.upper(), difficulty, marks),
        ).lastrowid


def get_questions(category_id=None):
    sql = ("SELECT q.*, c.name AS category FROM questions q JOIN categories c ON c.id = q.category_id")
    params = ()
    if category_id:
        sql += " WHERE q.category_id = ?"
        params = (category_id,)
    with get_connection() as conn:
        return conn.execute(sql + " ORDER BY q.id", params).fetchall()


def delete_question(question_id):
    with get_connection() as conn:
        return conn.execute("DELETE FROM questions WHERE id = ?", (question_id,)).rowcount


def random_questions(category_id, n):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM questions WHERE category_id = ? ORDER BY RANDOM() LIMIT ?", (category_id, n)
        ).fetchall()


def import_from_csv(path):
    """CSV columns: category,question,option_a,option_b,option_c,option_d,correct[,difficulty,marks]"""
    added, skipped = 0, 0
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            try:
                correct = row["correct"].strip().upper()
                if correct not in ("A", "B", "C", "D"):
                    raise ValueError("bad correct option")
                cid = get_or_create_category(row["category"].strip())
                add_question(
                    cid, row["question"].strip(),
                    [row["option_a"].strip(), row["option_b"].strip(), row["option_c"].strip(), row["option_d"].strip()],
                    correct, (row.get("difficulty") or "medium").strip().lower(), int(row.get("marks") or 1),
                )
                added += 1
            except (KeyError, ValueError, AttributeError):
                skipped += 1
    return added, skipped


# ---------- admin UI ----------
def pick_category(allow_new=True):
    cats = get_categories()
    print_table(["ID", "Category", "Questions"], [(c["id"], c["name"], c["total"]) for c in cats])
    if allow_new:
        print("  Enter 0 to create a new category.")
    valid = {c["id"] for c in cats}
    while True:
        cid = ask_int("Category ID: ", 0 if allow_new else 1)
        if cid == 0 and allow_new:
            return get_or_create_category(ask("New category name: "))
        if cid in valid:
            return cid
        print("  No such category.")


def _add_question_ui():
    header("Add Question")
    cid = pick_category()
    text = ask("Question text: ")
    options = [ask(f"Option {l}: ") for l in "ABCD"]
    while True:
        correct = ask("Correct option (A/B/C/D): ").upper()
        if correct in ("A", "B", "C", "D"):
            break
        print("  Enter A, B, C or D.")
    difficulty = ask("Difficulty (easy/medium/hard) [medium]: ", allow_empty=True).lower() or "medium"
    marks = ask_int("Marks [1-10]: ", 1, 10)
    add_question(cid, text, options, correct, difficulty, marks)
    print("  Question added.")


def _list_questions_ui():
    header("Question List")
    rows = get_questions()
    print_table(
        ["ID", "Category", "Question", "Ans", "Level", "Marks"],
        [(q["id"], q["category"], q["text"][:45], q["correct_option"], q["difficulty"], q["marks"]) for q in rows],
    )


def _delete_question_ui():
    _list_questions_ui()
    qid = ask_int("Question ID to delete (0 to cancel): ", 0)
    if qid and confirm(f"Delete question {qid}?"):
        print("  Deleted." if delete_question(qid) else "  No such question.")


def _import_ui():
    header("Import Questions from CSV")
    print("  Columns: category,question,option_a,option_b,option_c,option_d,correct[,difficulty,marks]")
    path = Path(ask("CSV file path: ").strip('"'))
    if not path.exists():
        print("  File not found.")
        return
    added, skipped = import_from_csv(path)
    print(f"  Imported {added} question(s), skipped {skipped} invalid row(s).")


def menu():
    actions = {"1": _add_question_ui, "2": _list_questions_ui, "3": _delete_question_ui, "4": _import_ui}
    while True:
        header("Question Bank")
        print("  1. Add question\n  2. View all questions\n  3. Delete question\n  4. Import from CSV\n  5. Back")
        choice = ask("Choice: ")
        if choice == "5":
            return
        actions.get(choice, lambda: print("  Invalid choice."))()

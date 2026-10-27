"""Leaderboard: best attempt per student, ranked by score then speed."""
from database import get_connection
import exam_engine
from utils import ask_int, fmt_time, header, print_table


def exam_leaderboard(exam_id, limit=10):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT a.*, u.full_name FROM attempts a JOIN users u ON u.id = a.user_id "
            "WHERE a.exam_id = ? ORDER BY a.score DESC, a.time_taken_sec ASC", (exam_id,)
        ).fetchall()
    seen, best = set(), []
    for r in rows:
        if r["user_id"] not in seen:
            seen.add(r["user_id"])
            best.append(r)
    return best[:limit]


def overall_leaderboard(limit=10):
    """Sum of each student's best score in every exam."""
    with get_connection() as conn:
        exam_ids = [r["id"] for r in conn.execute("SELECT id FROM exams")]
        names = {r["id"]: r["full_name"] for r in conn.execute("SELECT id, full_name FROM users")}
    totals = {}
    for eid in exam_ids:
        for r in exam_leaderboard(eid, limit=10_000):
            t = totals.setdefault(r["user_id"], [0.0, 0, 0])
            t[0] += r["score"]
            t[1] += 1
            t[2] += r["time_taken_sec"]
    ranked = sorted(totals.items(), key=lambda kv: (-kv[1][0], kv[1][2]))[:limit]
    return [(names[uid], t[0], t[1], t[2]) for uid, t in ranked]


def show_leaderboard():
    header("Leaderboard")
    exams = exam_engine.list_exams()
    exam_engine.show_exams(exams)
    print("  Enter an exam ID, or 0 for the overall leaderboard.")
    eid = ask_int("Choice: ", 0)
    if eid == 0:
        rows = overall_leaderboard()
        print_table(["Rank", "Student", "Total Score", "Exams", "Total Time"],
                    [(i, n, s, c, fmt_time(t)) for i, (n, s, c, t) in enumerate(rows, 1)])
    elif eid in {e["id"] for e in exams}:
        rows = exam_leaderboard(eid)
        print_table(["Rank", "Student", "Score", "Time"],
                    [(i, r["full_name"], f"{r['score']}/{r['total_marks']}", fmt_time(r["time_taken_sec"]))
                     for i, r in enumerate(rows, 1)])
    else:
        print("  Invalid exam ID.")

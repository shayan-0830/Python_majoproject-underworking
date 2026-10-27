# Python_majoproject-underworking
the project is under working, some files are uploaded, not the full project
# Quiz / Online Exam System

A console-based online exam platform built with **Python** and **SQLite**. It supports an admin panel, a question bank, a timed test engine, automatic result generation and a leaderboard. It uses only the Python standard library, so there is nothing to install.

---

## Features

- **Admin panel** – manage questions, exams, students and results from one menu
- **Question bank** – categories, difficulty levels, marks per question, bulk import from CSV
- **Timer and test engine** – random question selection, time limit, auto-submit on timeout, negative marking
- **Result generation** – score, percentage, pass/fail, full answer review, saved text reports, CSV export
- **Leaderboard** – best attempt per student, ranked by score and then by time, per exam and overall
- **Authentication** – student registration and login with salted SHA-256 password hashing

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.8+ |
| Database | SQLite (`sqlite3` module) |
| Interface | Command line |
| Dependencies | None (standard library only) |

## Project Structure

```
quiz_exam_system/
├── main.py              # Entry point: login, registration, student dashboard
├── admin.py             # Admin panel menu
├── question_bank.py     # Categories, questions, CSV import, random selection
├── exam_engine.py       # Exam setup, timed session, scoring
├── results.py           # Result report, answer review, history, exports
├── leaderboard.py       # Per-exam and overall rankings
├── database.py          # SQLite schema, password hashing, sample data
├── utils.py             # Input validation and table printing helpers
├── sample_questions.csv # Example file for bulk import
└── README.md
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/quiz-exam-system.git
cd quiz-exam-system
```

### 2. Run the application

```bash
python main.py
```

The database (`quiz_system.db`) is created automatically on the first run, along with a sample "Python Basics" exam containing 10 questions.

### 3. Log in

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Student | Register from the main menu | Your choice (min 6 characters) |

> Change the default admin password before using this anywhere other than a local demo.

## How to Use

**Admin**
1. Log in as `admin`.
2. Open **Question bank** to add questions one by one or import a CSV.
3. Open **Manage exams** to create an exam: pick a category, number of questions, duration and negative marking.
4. Use **View all results**, **Leaderboard** and **Export results to CSV** to monitor performance.

**Student**
1. Register, then log in.
2. Choose **Take an exam**, select an exam and press Enter to start.
3. Answer with `A`, `B`, `C` or `D`, or `S` to skip a question.
4. The result is shown immediately and a report is saved in the `reports/` folder.

## CSV Import Format

The first row must be the header:

```csv
category,question,option_a,option_b,option_c,option_d,correct,difficulty,marks
Computer Basics,Which of these is an input device?,Monitor,Keyboard,Printer,Speaker,B,easy,1
```

`difficulty` and `marks` are optional (defaults: `medium`, `1`). Invalid rows are skipped and counted in the import summary.

## How It Works

**Scoring**
- Correct answer: `+marks`
- Wrong answer: `−(negative_marking × marks)`
- Skipped: `0`
- The final score never goes below 0. The pass mark is 40% (set by `PASS_PERCENT` in `results.py`).

**Timer**
The remaining time is shown on every question. Because console `input()` cannot be interrupted, the deadline is checked after each answer: an answer submitted after time expires is not counted and the test is auto-submitted.

**Leaderboard**
Each student's best attempt per exam is used. Ties are broken by the shorter time taken. The overall leaderboard adds up each student's best score across all exams.

## Database Schema

| Table | Purpose |
|---|---|
| `users` | Admin and student accounts (hashed passwords) |
| `categories` | Question categories |
| `questions` | Question text, four options, correct option, difficulty, marks |
| `exams` | Exam title, category, number of questions, duration, negative marking, visibility |
| `attempts` | One row per completed test with score and time taken |
| `attempt_answers` | The option chosen for each question in an attempt |

## Future Enhancements

- GUI or web front end (Tkinter or Flask) with a live countdown timer
- Per-question timers and option shuffling
- Question editing from the admin panel
- Password change and reset
- Charts for result analysis

## Author

**Mohammad Shayan Ansari**
GitHub: [@your-username](https://github.com/your-username)

## License

This project is for educational purposes. Add a license of your choice (for example MIT) before publishing.

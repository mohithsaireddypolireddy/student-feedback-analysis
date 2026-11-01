from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from io import BytesIO
import csv

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "feedback.db"
CHART_DIR = BASE_DIR / "static" / "charts"
CHART_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = "change-this-demo-secret-key"

COURSES = [
    ("Python Programming", "Dr. Ananya Rao"),
    ("Data Structures", "Prof. Kiran Kumar"),
    ("Computer Networks", "Dr. Meera Sharma"),
    ("Database Management", "Prof. Arjun Reddy"),
]
QUESTIONS = [
    "The course content was well organized.",
    "Explanations were clear and easy to follow.",
    "Learning materials were useful.",
    "The pace of the course was appropriate.",
    "Overall, I am satisfied with this course.",
]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL UNIQUE,
            faculty_name TEXT NOT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS feedback_questions (
            question_id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT NOT NULL UNIQUE
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS feedback (
            feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            comment_optional TEXT,
            submitted_at TEXT NOT NULL,
            FOREIGN KEY(course_id) REFERENCES courses(course_id),
            FOREIGN KEY(question_id) REFERENCES feedback_questions(question_id)
        )""")
        for name, faculty in COURSES:
            conn.execute("INSERT OR IGNORE INTO courses(course_name, faculty_name) VALUES (?, ?)", (name, faculty))
        for question in QUESTIONS:
            conn.execute("INSERT OR IGNORE INTO feedback_questions(question_text) VALUES (?)", (question,))

def query_df(sql, params=()):
    with get_db() as conn:
        return pd.read_sql_query(sql, conn, params=params)

def dashboard_data():
    courses = query_df("SELECT * FROM courses ORDER BY course_name")
    stats = query_df("""SELECT COUNT(*) AS responses, ROUND(AVG(rating), 2) AS avg_rating,
                         COUNT(DISTINCT course_id) AS courses_count FROM feedback""").iloc[0].to_dict()
    if stats["avg_rating"] is None:
        stats["avg_rating"] = 0
    course_summary = query_df("""SELECT c.course_id, c.course_name, c.faculty_name,
        COUNT(f.feedback_id) AS response_count, ROUND(AVG(f.rating), 2) AS avg_rating
        FROM courses c LEFT JOIN feedback f ON c.course_id=f.course_id
        GROUP BY c.course_id ORDER BY c.course_name""")
    course_summary["avg_rating"] = course_summary["avg_rating"].fillna(0)
    return courses, stats, course_summary

@app.route("/")
def index():
    courses, stats, summary = dashboard_data()
    dist = query_df("SELECT rating, COUNT(*) AS count FROM feedback GROUP BY rating ORDER BY rating")
    distribution = {str(i): 0 for i in range(1, 6)}
    for _, row in dist.iterrows():
        distribution[str(int(row["rating"]))] = int(row["count"])
    return render_template("index.html", courses=courses.to_dict("records"), stats=stats,
                           summary=summary.to_dict("records"), distribution=distribution)

@app.route("/feedback", methods=["GET", "POST"])
def feedback_form():
    courses, _, _ = dashboard_data()
    questions = query_df("SELECT * FROM feedback_questions ORDER BY question_id")
    if request.method == "POST":
        try:
            course_id = int(request.form.get("course_id", ""))
            comment = request.form.get("comment", "").strip()
            if len(comment) > 500:
                raise ValueError("Optional comment must be 500 characters or fewer.")
            ratings = []
            for q in questions.to_dict("records"):
                raw = request.form.get(f"q_{q['question_id']}", "")
                rating = int(raw)
                if rating not in range(1, 6):
                    raise ValueError("Please select a rating from 1 to 5 for every question.")
                ratings.append((q["question_id"], rating))
            with get_db() as conn:
                valid_course = conn.execute("SELECT course_id FROM courses WHERE course_id=?", (course_id,)).fetchone()
                if not valid_course:
                    raise ValueError("Please choose a valid course.")
                timestamp = datetime.now().isoformat(timespec="seconds")
                conn.executemany("""INSERT INTO feedback(course_id, question_id, rating, comment_optional, submitted_at)
                                    VALUES (?, ?, ?, ?, ?)""",
                                 [(course_id, qid, rating, comment or None, timestamp) for qid, rating in ratings])
            flash("Thanks! Your anonymous feedback has been submitted.", "success")
            return redirect(url_for("feedback_form"))
        except (ValueError, TypeError):
            flash("Please complete all ratings correctly. Ratings must be between 1 and 5.", "error")
    return render_template("feedback.html", courses=courses.to_dict("records"), questions=questions.to_dict("records"))

@app.route("/reports")
def reports():
    by_question = query_df("""SELECT c.course_name, q.question_text, ROUND(AVG(f.rating), 2) AS avg_rating,
        COUNT(f.feedback_id) AS responses FROM feedback f
        JOIN courses c ON c.course_id=f.course_id JOIN feedback_questions q ON q.question_id=f.question_id
        GROUP BY c.course_id, q.question_id ORDER BY c.course_name, q.question_id""")
    summary = query_df("""SELECT c.course_name, COUNT(f.feedback_id) AS rating_count,
        ROUND(AVG(f.rating), 2) AS avg_rating FROM courses c LEFT JOIN feedback f ON c.course_id=f.course_id
        GROUP BY c.course_id ORDER BY c.course_name""")
    summary["avg_rating"] = summary["avg_rating"].fillna(0)
    return render_template("reports.html", by_question=by_question.to_dict("records"),
                           summary=summary.to_dict("records"))

@app.route("/charts/course.png")
def course_chart():
    df = query_df("""SELECT c.course_name, AVG(f.rating) AS avg_rating FROM courses c
        LEFT JOIN feedback f ON c.course_id=f.course_id GROUP BY c.course_id ORDER BY c.course_name""")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = ["#6c63ff", "#18b6a4", "#ffb84d", "#ff6b8a", "#4e9cff"]
    vals = df["avg_rating"].fillna(0).to_numpy(dtype=float)
    bars = ax.bar(df["course_name"], vals, color=colors[:len(df)], width=.62, edgecolor="white")
    ax.set_ylim(0, 5)
    ax.set_ylabel("Average rating (1–5)")
    ax.set_title("Course satisfaction comparison", pad=16, weight="bold")
    ax.grid(axis="y", alpha=.2)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", rotation=15)
    for bar, val in zip(bars, vals):
        if val > 0:
            ax.text(bar.get_x()+bar.get_width()/2, val+.08, f"{val:.2f}", ha="center", fontsize=9)
    fig.tight_layout()
    return chart_response(fig)

@app.route("/charts/distribution.png")
def distribution_chart():
    df = query_df("SELECT rating, COUNT(*) AS count FROM feedback GROUP BY rating ORDER BY rating")
    counts = {i: 0 for i in range(1, 6)}
    for _, row in df.iterrows():
        counts[int(row["rating"])] = int(row["count"])
    fig, ax = plt.subplots(figsize=(7, 4))
    vals = [counts[i] for i in range(1, 6)]
    ax.bar(["1 star", "2 stars", "3 stars", "4 stars", "5 stars"], vals,
           color=["#ff6b8a", "#ff9f68", "#ffc857", "#42c8a5", "#6c63ff"], width=.62)
    ax.set_ylabel("Number of ratings")
    ax.set_title("Overall rating distribution", pad=16, weight="bold")
    ax.grid(axis="y", alpha=.2)
    ax.set_axisbelow(True)
    fig.tight_layout()
    return chart_response(fig)

def chart_response(fig):
    from flask import make_response
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    response = make_response(buf.read())
    response.headers["Content-Type"] = "image/png"
    response.headers["Cache-Control"] = "no-store"
    return response

@app.route("/export.csv")
def export_csv():
    df = query_df("""SELECT c.course_name, q.question_text, ROUND(AVG(f.rating), 2) AS average_rating,
        COUNT(f.feedback_id) AS response_count FROM feedback f
        JOIN courses c ON c.course_id=f.course_id JOIN feedback_questions q ON q.question_id=f.question_id
        GROUP BY c.course_id, q.question_id ORDER BY c.course_name, q.question_id""")
    output = BytesIO()
    output.write(df.to_csv(index=False).encode("utf-8-sig"))
    output.seek(0)
    return send_file(output, mimetype="text/csv", as_attachment=True, download_name="course_feedback_summary.csv")

@app.route("/demo-data", methods=["POST"])
def demo_data():
    # Explicitly synthetic demo data; no real student identities are stored.
    rng = np.random.default_rng(42)
    with get_db() as conn:
        existing = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
        if existing == 0:
            courses = conn.execute("SELECT course_id FROM courses ORDER BY course_id").fetchall()
            questions = conn.execute("SELECT question_id FROM feedback_questions ORDER BY question_id").fetchall()
            rows = []
            for course in courses:
                for _ in range(12):
                    for q in questions:
                        rating = int(np.clip(round(rng.normal(4.0, .8)), 1, 5))
                        rows.append((course["course_id"], q["question_id"], rating, None, datetime.now().isoformat(timespec="seconds")))
            conn.executemany("INSERT INTO feedback(course_id, question_id, rating, comment_optional, submitted_at) VALUES (?, ?, ?, ?, ?)", rows)
            flash("Synthetic demo data added. You can now explore charts and reports.", "success")
        else:
            flash("Demo data is only added when the database is empty. Existing feedback was left unchanged.", "error")
    return redirect(url_for("index"))

@app.route("/clear-demo", methods=["POST"])
def clear_data():
    with get_db() as conn:
        conn.execute("DELETE FROM feedback")
    flash("All feedback records were cleared from this local demo database.", "success")
    return redirect(url_for("index"))

@app.route("/api/summary")
def api_summary():
    _, stats, summary = dashboard_data()
    return {"stats": stats, "courses": summary.to_dict("records")}

init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)

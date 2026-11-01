# Student Feedback Analysis System

A beginner-friendly Flask web app with a colourful, responsive dashboard, animated UI interactions, anonymous numeric feedback, course/question summaries, charts, CSV export, and synthetic demo data.

## Features
- Anonymous course feedback form with 1–5 rating validation
- SQLite local database (easy to run; no MySQL setup needed)
- Dashboard with response counts, average ratings, and course summaries
- Matplotlib charts: course comparison and rating distribution
- Pandas/NumPy analysis and aggregated CSV export
- Responsive design, animated cards, hover states, progress indicators, and reduced-motion support
- Synthetic demo data button to explore the dashboard immediately

## Run in VS Code (Mac / Windows / Linux)

### 1. Open the project
Extract the ZIP, open VS Code, then choose **File → Open Folder** and select `student_feedback_analysis`.

### 2. Create a virtual environment
Open **Terminal → New Terminal** inside VS Code.

**Mac/Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell**
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install packages
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Start the app
```bash
python app.py
```
Open **http://127.0.0.1:5000** in your browser.

### 5. Explore
- Click **Add demo data** on the dashboard to populate synthetic ratings.
- Open **Give feedback** to submit a new anonymous response.
- Open **Reports** to view course/question averages.
- Click **Export CSV** to download aggregated results.

## Reset local data
Use the **Clear feedback data** button on the dashboard to clear feedback rows. This action cannot be undone. The app does not store student names, email addresses, or student IDs.

## Database
SQLite database file `feedback.db` is created automatically on first run. Tables:
- `courses(course_id, course_name, faculty_name)`
- `feedback_questions(question_id, question_text)`
- `feedback(feedback_id, course_id, question_id, rating, comment_optional, submitted_at)`

The timestamp is stored for basic recordkeeping, but the UI does not expose individual records or comments. Reports are aggregated. For a real deployment, add authentication/authorization, CSRF protection, production server configuration, database backups, and suppression of small-group results.

## Notes
- This is a local educational/demo project, not a production-ready institutional system.
- The dashboard uses anonymous or synthetic feedback and avoids publishing comments.

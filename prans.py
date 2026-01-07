from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import calendar

app = Flask(__name__)
app.secret_key = "supersecretkey"
DB_FILE = "events.db"

# Database helper
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# Home route
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

# Register route
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        confirm = request.form["confirm_password"]

        if not username or not password or not confirm:
            flash("Please fill in all fields.", "error")
            return redirect(url_for("register"))

        if password != confirm:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))

        conn = get_db_connection()
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            flash("Username already taken.", "error")
            conn.close()
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)
        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()

        flash("Account successfully created! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

# Logout route
@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "success")
    return redirect(url_for("login"))

# Dashboard route
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Get month/year for calendar
    year = request.args.get("year", type=int, default=datetime.now().year)
    month = request.args.get("month", type=int, default=datetime.now().month)

    # Month navigation
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    month_name = calendar.month_name[month]

    # Flatten calendar for grid
    cal = calendar.Calendar(firstweekday=0)
    month_days_flat = [day for week in cal.monthdayscalendar(year, month) for day in week]

    conn = get_db_connection()
    events = conn.execute("SELECT * FROM events").fetchall()

    # Map days to events
    events_by_day = {}
    for event in events:
        y, m, d = map(int, event["event_date"].split("-"))
        if y == year and m == month:
            if d not in events_by_day:
                events_by_day[d] = []
            events_by_day[d].append(event)

    # User registrations
    registrations = conn.execute("""
        SELECT e.name, e.event_date FROM registrations r
        JOIN events e ON r.event_id = e.id
        WHERE r.user_id = ?
        ORDER BY e.event_date
    """, (session["user_id"],)).fetchall()

    conn.close()

    return render_template("dashboard.html",
                           username=session["username"],
                           month=month,
                           year=year,
                           prev_month=prev_month,
                           prev_year=prev_year,
                           next_month=next_month,
                           next_year=next_year,
                           month_name=month_name,
                           month_days_flat=month_days_flat,
                           events_by_day=events_by_day,
                           registrations=registrations)

# Add event route
@app.route("/add_event", methods=["GET", "POST"])
def add_event():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"].strip()
        event_date = request.form["event_date"]

        if not name or not event_date:
            flash("Please provide event name and date.", "error")
            return redirect(url_for("add_event"))

        conn = get_db_connection()
        conn.execute("INSERT INTO events (name, event_date, created_by) VALUES (?, ?, ?)",
                     (name, event_date, session["user_id"]))
        conn.commit()
        conn.close()
        flash("Event added successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_event.html")

# Register for event
@app.route("/register_event/<int:event_id>")
def register_event(event_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM registrations WHERE user_id = ? AND event_id = ?",
                            (session["user_id"], event_id)).fetchone()
    if existing:
        flash("You are already registered for this event.", "error")
        conn.close()
        return redirect(url_for("dashboard"))

    conn.execute("INSERT INTO registrations (user_id, event_id) VALUES (?, ?)", (session["user_id"], event_id))
    conn.commit()
    conn.close()
    flash("Registered for event successfully!", "success")
    return redirect(url_for("dashboard"))

# View events by day
@app.route("/events/<int:year>/<int:month>/<int:day>")
def events_by_day(year, month, day):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    events = conn.execute("SELECT * FROM events WHERE event_date = ?",
                          (f"{year:04d}-{month:02d}-{day:02d}",)).fetchall()
    conn.close()

    return render_template("events_by_day.html", events=events, day=day, month=month, year=year)

if __name__ == "__main__":
    app.run(debug=True)

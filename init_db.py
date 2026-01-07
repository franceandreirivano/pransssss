import sqlite3
from werkzeug.security import generate_password_hash
import os

DB_FILE = "events.db"

# Remove old database if exists
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)
    print("Old database deleted.")

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Users table
cursor.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# Events table
cursor.execute("""
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    event_date TEXT NOT NULL,
    created_by INTEGER,
    FOREIGN KEY(created_by) REFERENCES users(id)
)
""")

# Registrations table
cursor.execute("""
CREATE TABLE registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(event_id) REFERENCES events(id)
)
""")

# Sample users
users = [
    ("alice", generate_password_hash("password123")),
    ("bob", generate_password_hash("mypassword"))
]
cursor.executemany("INSERT INTO users (username, password) VALUES (?, ?)", users)

# Sample events
events = [
    ("Python Workshop", "2026-02-01", 1),
    ("Data Science Seminar", "2026-02-15", 2),
    ("AI Conference", "2026-03-05", 1)
]
cursor.executemany("INSERT INTO events (name, event_date, created_by) VALUES (?, ?, ?)", events)

conn.commit()
conn.close()
print("Database created successfully!")

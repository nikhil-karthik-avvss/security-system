import sqlite3

conn = sqlite3.connect("security_events.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    zone TEXT,
    motion INTEGER,
    light INTEGER,
    distance REAL,
    sound INTEGER,
    threat INTEGER,
    level TEXT,
    image TEXT
)
""")

conn.commit()
conn.close()

print("Database ready")

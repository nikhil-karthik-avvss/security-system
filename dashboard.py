from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

def get_events():
    conn = sqlite3.connect("security_events.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT timestamp, zone, threat, level, image
        FROM events
        ORDER BY id DESC
        LIMIT 50
    """)

    rows = cur.fetchall()
    conn.close()

    return rows


@app.route("/")
def home():
    events = get_events()
    return render_template("dashboard.html", events=events)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

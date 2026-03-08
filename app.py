import json
import sqlite3
import random
import threading
import paho.mqtt.client as mqtt
from flask import Flask, render_template

BROKER = "broker.hivemq.com"
TOPIC = "ssn/campus/security"

images = [
"intruder1.jpg",
"intruder2.jpg",
"intruder3.jpg"
]

app = Flask(__name__)

conn = sqlite3.connect("security_events.db", check_same_thread=False)
cur = conn.cursor()


def init_db():

    cur.execute("""
    CREATE TABLE IF NOT EXISTS events(
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


def on_connect(client, userdata, flags, rc):
    print("MQTT Connected")
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):

    data = json.loads(msg.payload.decode())

    zone = data["zone"]
    motion = data["motion"]
    light = data["light"]
    distance = data["distance"]
    sound = data["sound"]
    threat = data["threat"]
    level = data["level"]

    image = None

    if level == "HIGH":
        image = random.choice(images)

    cur.execute("""
    INSERT INTO events(zone,motion,light,distance,sound,threat,level,image)
    VALUES(?,?,?,?,?,?,?,?)
    """,(zone,motion,light,distance,sound,threat,level,image))

    conn.commit()

    print("Stored:",zone,level)


def start_mqtt():

    client = mqtt.Client()

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER,1883,60)

    client.loop_forever()


@app.route("/")
def dashboard():

    cur.execute("""
    SELECT timestamp,zone,threat,level,image
    FROM events
    ORDER BY id DESC
    LIMIT 30
    """)

    rows = cur.fetchall()

    high_zones = [r[1] for r in rows if r[3]=="HIGH"]

    return render_template("dashboard.html",
                           events=rows,
                           alerts=high_zones)


if __name__ == "__main__":

    init_db()

    mqtt_thread = threading.Thread(target=start_mqtt)
    mqtt_thread.daemon = True
    mqtt_thread.start()

    app.run(host="0.0.0.0",port=10000)
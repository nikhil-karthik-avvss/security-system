import json
import sqlite3
import random
import threading
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
from flask import Flask, render_template

BROKER = "broker.hivemq.com"
TOPIC = "ssn/campus/security"

app = Flask(__name__)

conn = sqlite3.connect("security_events.db", check_same_thread=False)
cur = conn.cursor()

images = [
"intruder1.jpg",
"intruder2.jpg",
"intruder3.jpg"
]

ZONE_COORDS = {
"CSE Department": (641,277),
"CSE Annexure": (635,253),
"Gents Hostel 1": (730,279),
"Gents Hostel 2": (697,280),
"Gents Hostel 3": (737,317),
"Gents Hostel 4": (710,322),
"Gents Hostel 5": (724,348),
"Gents Hostel 6": (763,329),
"Gents Hostel 7": (736,367),
"Gents Hostel 8": (732,388),
"Gents Hostel 9": (695,377),
"Open Air Theatre": (667,273),
"Hostel Ground": (733,254),
"CSE Parking Lot": (655,253),
"Library": (590,274),
"Old ECE Block": (608,305),
"IT Block": (618,268),
"New ECE Block": (590,317),
"ECE Annexure": (578,305),
"Fountain": (570,266),
"Admin Block": (551,257),
"CDC Block": (596,243),
"Ladies Hostel 1": (533,171),
"Ladies Hostel 2": (542,155),
"Ladies Hostel 3": (553,177),
"Ladies Hostel 4": (563,167),
"Ladies Hostel 5": (587,179),
"Ladies Hostel 6": (572,149),
"Ladies Hostel 7": (529,161),
"Clock Tower": (600,210),
"Vama Sundari Park": (643,222),
"Rishabh's Canteen": (548,287),
"The MetroCafe": (518,189),
"Ashwin's Food Court": (611,182),
"Main Canteen": (516,185),
"Food Swingers": (517,182),
"SNU Academic Block 1": (459,231),
"SNU Academic Block 2": (439,259),
"SNU Academic Block 3": (435,231),
"SNU Academic Block 4": (414,238),
"Sports Complex": (490,205),
"Main Gate": (907,263),
"School of Management Block": (715,198),
"School of Advanced Secondary Education Block": (867,229),
"The Temple": (892,244),
"Bus Bay": (917,229),
"Mechanical Bus Bay": (541,230),
"Mechanical Block": (508,250),
"Mechanical Department Workshop": (473,292),
"Mini Auditorium": (492,303),
"Physics Chemistry Block": (478,322),
"EEE Block": (587,377),
"BME Block": (669,374),
"PR Food Court": (626,363),
"Chemical Block": (640,380),
"Civil Block": (614,374),
"HCL Healthcare": (678,392),
"Main Auditorium": (769,208),
"Football Ground": (357,210),
"Cricket Stadium": (303,237),
"Rear Gate": (29,333)
}

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
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):

    data=json.loads(msg.payload.decode())

    zone=data["zone"]
    motion=data["motion"]
    light=data["light"]
    distance=data["distance"]
    sound=data["sound"]
    threat=data["threat"]
    level=data["level"]

    image=None

    if level=="HIGH":
        image=random.choice(images)

    cur.execute("""
    INSERT INTO events(zone,motion,light,distance,sound,threat,level,image)
    VALUES(?,?,?,?,?,?,?,?)
    """,(zone,motion,light,distance,sound,threat,level,image))

    conn.commit()

def start_mqtt():

    client=mqtt.Client()

    client.on_connect=on_connect
    client.on_message=on_message

    client.connect(BROKER,1883,60)

    client.loop_forever()


def detect_anomalies():

    cur.execute("""
    SELECT zone,COUNT(*)
    FROM events
    WHERE timestamp >= datetime('now','-10 minutes')
    GROUP BY zone
    """)

    recent=dict(cur.fetchall())

    cur.execute("""
    SELECT zone,COUNT(*)
    FROM events
    GROUP BY zone
    """)

    total=dict(cur.fetchall())

    anomalies=[]

    for zone,rcount in recent.items():

        hcount=total.get(zone,0)

        if rcount>=3 and rcount>(hcount*0.3):

            if zone in ZONE_COORDS:

                x,y=ZONE_COORDS[zone]

                anomalies.append({
                    "zone":zone,
                    "x":x,
                    "y":y,
                    "count":rcount
                })

    return anomalies


@app.route("/")
def dashboard():

    cur.execute("""
    SELECT timestamp,zone,threat,level,image
    FROM events
    ORDER BY id DESC
    LIMIT 50
    """)

    rows=cur.fetchall()

    markers=[]
    replay=[]

    for r in rows:

        zone=r[1]
        level=r[3]

        if zone in ZONE_COORDS:

            x,y=ZONE_COORDS[zone]

            markers.append({
                "zone":zone,
                "x":x,
                "y":y,
                "level":level
            })

            replay.append({
                "zone":zone,
                "x":x,
                "y":y,
                "level":level
            })

    cur.execute("""
    SELECT zone,COUNT(*)
    FROM events
    GROUP BY zone
    """)

    heat=cur.fetchall()

    heatmap=[]

    for h in heat:

        zone=h[0]
        count=h[1]

        if zone in ZONE_COORDS:

            x,y=ZONE_COORDS[zone]

            heatmap.append({
                "zone":zone,
                "x":x,
                "y":y,
                "count":count
            })

    cur.execute("""
    SELECT zone,COUNT(*)
    FROM events
    GROUP BY zone
    ORDER BY COUNT(*) DESC
    LIMIT 5
    """)

    stats=cur.fetchall()

    zones=[s[0] for s in stats]
    counts=[s[1] for s in stats]

    anomalies=detect_anomalies()

    return render_template(
        "dashboard.html",
        events=rows,
        markers=markers,
        zones=zones,
        counts=counts,
        replay=replay,
        heatmap=heatmap,
        anomalies=anomalies
    )

if __name__=="__main__":

    init_db()

    mqtt_thread=threading.Thread(target=start_mqtt)
    mqtt_thread.daemon=True
    mqtt_thread.start()

    app.run(host="0.0.0.0",port=10000)
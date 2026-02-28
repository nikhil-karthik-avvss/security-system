import json
import sqlite3
import random
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
TOPIC = "ssn/campus/security"

images = [
    "intruder1.jpg",
    "intruder2.jpg",
    "intruder3.jpg",
    "intruder4.jpg"
]

conn = sqlite3.connect("security_events.db", check_same_thread=False)
cur = conn.cursor()

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT")
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

    print("Event stored:", zone, level, image)

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER,1883,60)

client.loop_forever()

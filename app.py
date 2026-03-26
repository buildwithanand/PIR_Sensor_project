import serial, sqlite3, threading
from datetime import datetime
from flask import Flask, jsonify, render_template

# === Serial Config ===
PORT = 'COM4'    # Change to your actual port
BAUD = 9600      # Must match Arduino Serial.begin(9600)

# === Database ===
db = sqlite3.connect('motion_logs.db', check_same_thread=False)
cur = db.cursor()
cur.execute('''
CREATE TABLE IF NOT EXISTS logs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TEXT,
    end_time TEXT,
    duration REAL
)
''')
db.commit()

app = Flask(__name__)

current_start = None  # Track when light turned ON


# === Parse Arduino Output ===
def handle_line(line):
    global current_start
    line = line.strip()

    if "→ Light turned ON" in line:
        current_start = datetime.now()
        print(f"[{current_start}] Light turned ON")

    elif "→ Light turned OFF" in line and current_start:
        end_time = datetime.now()
        duration = (end_time - current_start).total_seconds()
        cur.execute('INSERT INTO logs(start_time, end_time, duration) VALUES (?, ?, ?)',
                    (current_start.isoformat(), end_time.isoformat(), duration))
        db.commit()
        print(f"[{end_time}] Light turned OFF (Duration: {duration:.1f}s)")
        current_start = None


# === Background Serial Reader ===
def read_serial():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
        print(f"✅ Connected to {PORT}")
    except Exception as e:
        print("❌ Serial error:", e)
        return

    while True:
        try:
            line = ser.readline().decode(errors='ignore').strip()
            if line:
                handle_line(line)
        except Exception as e:
            print("Read error:", e)


# Start serial reading in background
t = threading.Thread(target=read_serial, daemon=True)
t.start()


# === Flask Routes ===
@app.route('/api/logs')
def api_logs():
    rows = cur.execute('SELECT * FROM logs ORDER BY id DESC LIMIT 50').fetchall()
    data = [{"id": r[0], "start": r[1], "end": r[2], "duration": r[3]} for r in rows]
    return jsonify(data)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True, port=5000)

import serial, time

try:
    arduino = serial.Serial('COM4', 9600, timeout=1)
    time.sleep(2)
    print("✅ Connected to Arduino successfully!")
except Exception as e:
    arduino = None
    print(f"❌ Serial error: {e}")


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)

import serial

try:
    ser = serial.Serial('COM4', 9600)
    print("✅ Connected to COM4")
except serial.SerialException as e:
    print(f"❌ Serial error: {e}")
    ser = None

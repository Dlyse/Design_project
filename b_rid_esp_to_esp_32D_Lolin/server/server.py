import serial                                               # allows data reading from ESP32 via USB
import json                                                 # parses JSON strings into dictionaries
import threading                                            # lets Serial reader and web server run simultaneously
from flask import Flask, jsonify, render_template_string    # Flask is the web framework, jsonify converts dicts to JSON response, render_template_string allows direct HTML writing in the python file

app = Flask(__name__)

# dictonary to hold most recent drone data, initialise with placeholder values
latest_data = {
    "id": "Waiting...",     # ID
    "lat": 0,               # latitude
    "lon": 0,               # longitude
    "alt": 0,               # altitude
    "rssi": 0,              # Received Signal Strength Indicator
    "last_seen": "Never",
}

########################################################### HTML DASHBOARD ###########################################################

# basically just a regular HTML page stored in a python string
# loads values from latest_data
# [meta http-equiv="refresh" content="1"] refreshes the page in the browser every second

DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
  <title>drone go weeeeeeeeeeeee</title>
  <meta http-equiv="refresh" content="1"> <!-- auto-refresh every second -->
  <style>
    body { font-family: Arial, sans-serif; padding: 40px; background: #f4f4f4; }
    h1   { color: #333; }
    .card { background: white; padding: 20px; border-radius: 8px; 
            max-width: 400px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
    .field { margin: 10px 0; font-size: 1.1em; }
    .label { font-weight: bold; color: #555; }
  </style>
</head>
<body>
  <h1>Drone Status</h1>
  <div class="card">
    <div class="field"><span class="label">Drone ID:</span> {{ data.id }}</div>
    <div class="field"><span class="label">Latitude:</span> {{ data.lat }}</div>
    <div class="field"><span class="label">Longitude:</span> {{ data.lon }}</div>
    <div class="field"><span class="label">Altitude:</span> {{ data.alt }} m</div>
    <div class="field"><span class="label">RSSI:</span> {{ data.rssi }} dBm</div>
    <div class="field"><span class="label">Last Seen:</span> {{ data.last_seen }}</div>
  </div>
</body>
</html>
"""

########################################################### ROUTES ###########################################################

# first line tells Flask to run the function below when someone requests the root URL
# this renders the dashboard and passes the current latest_data, which fills in the page
@app.route("/")
def index():
    return render_template_string(DASHBOARD, data=latest_data)

# returns raw JSON file (for debugging purposes)
@app.route("/data")
def data():
    return jsonify(latest_data)

########################################################### SERIAL PORT READER ###########################################################

# function to constantly listen to the relevant serial port from Arduino
# [.decode("utf-8").strip()] converts raw bytes into a string (also removes any whitespaces)
# [if line.startswith("{"):] filters out any non-JSON lines, the code inside that if-statement just updates the data dictionary

def read_serial_port():
    cereal = serial.Serial("COM3", 115200, timeout=1)

    while True:
        try:
            line = cereal.readline().decode("utf-8").strip()
            if line.startswith("{"):
                parsed = json.loads(line)
                latest_data.update(parsed)
        except Exception as exception:
            print("Error reading serial port: ", exception)

########################################################### ENTRY POINT ###########################################################

# Create background thread running the read_serial_port function
# [daemon=True] just means that the process stops with the main program stops
# [app.run(host="0.0.0.0", port=5000, debug=False)] starts up the Flask web server, with the host set to 0.0.0.0 to ensure any device on the same network can access it

if __name__ == "__main__":
    thread = threading.Thread(target=read_serial_port, daemon=True)
    thread.start()
    app.run(host="0.0.0.0", port=5000, debug=False)
import serial                                               # allows data reading from ESP32 via USB
import json                                                 # parses JSON strings into dictionaries
import threading                                            # lets Serial reader and web server run simultaneously
from flask import Flask, jsonify, render_template_string    # Flask is the web framework, jsonify converts dicts to JSON response, render_template_string allows direct HTML writing in the python file

app = Flask(__name__)

# dictonary to hold most recent drone data, initialise with placeholder values
latest_data = {
    "id": "placeholder text",     # ID
    "lat": 0,               # latitude
    "lon": 0,               # longitude
    "alt": 0,               # altitude
    "rssi": 0,              # Received Signal Strength Indicator
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

########################################################### ROUTES FOR DATA ###########################################################

# first line tells Flask to run the function below when someone requests the root URL
# this renders the dashboard and passes the current latest_data, which fills in the page
@app.route("/")
def index():
    return render_template_string(DASHBOARD, data=latest_data)

# returns raw JSON file (for debugging purposes)
@app.route("/data")
def data():
    return jsonify(latest_data)

########################################################### POST ENDPOINT ###########################################################

# receives data from the ESP32 over Wi-Fi instead of via WIRED Serial Point connection
# methods=["POST"] ensures that only HTTP POST requests go through
# [request.get_json()] reads the JSON body from ESP32
# if valid JSON, update latest_data accordingly
# Returns an "OK" response with HTTP status "200" for confirmation purposes

@app.route("/post", methods=["POST"])
def receive_data():
    data = request.get_json()
    if data:
        latest_data.update(data)
        print("Received:", data)
    return "OK", 200

########################################################### ENTRY POINT ###########################################################

# [app.run(host="0.0.0.0", port=5000, debug=False)] starts up the Flask web server
# host set to 0.0.0.0 to ensure any device on the same network can access it
# Flask automatically handles incoming POST requests & browser visits accordingly


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
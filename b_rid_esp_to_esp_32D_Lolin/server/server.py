import json                                                         # parses JSON strings into dictionaries
import math                                                         # for buffer distance calculations
from flask import Flask, jsonify, render_template_string, request   # Flask is the web framework, jsonify converts dicts to JSON response, render_template_string allows direct HTML writing in the python file

app = Flask(__name__)

############################################################ ROUTE DEFINITION ############################################################

# here is a collection of predefined GPS waypoints along the planned delivery route
# format is latitude then longitude
ROUTE = [
    (1.3322723838302757, 103.7769543756633), 
    (1.3323056379195635, 103.77696042349615), 
    (1.3323524959537192, 103.77696042349615), 
    (1.3324114463825143, 103.77694983978864), 
    (1.332446212019359, 103.77694227999754), 
    (1.3325172548409232, 103.77695588762151), 
    (1.3325701590684227, 103.77695588762151), 
    (1.332600390055053, 103.77695588762151), 
    (1.3326457365342985, 103.77696042349615), 
    (1.332678990618561, 103.77696647132905), 
    (1.332710733153117, 103.77696193545438), 
    (1.3327591027287864, 103.7769710072037), 
    (1.3328165415986508, 103.77696798328725)
]

# drone should stay within 5m of the route at all times
BUFFER_METERS = 20

# calculates straight-line distance in metres between two GPS coordinates using flat geometry approximation (Pythagorean theorem on a plane)
# Assumes coordinates are in degrees and converts to meters using a simple scale factor
def distance_meters(lat1, lon1, lat2, lon2):
    # Approximate conversion: 1 degree of latitude ≈ 111,320 meters
    # 1 degree of longitude ≈ 111,320 * cos(latitude) meters
    # Using the average latitude for better accuracy
    avg_lat = (lat1 + lat2) / 2
    lat_scale = 111320  # meters per degree of latitude
    lon_scale = 111320 * math.cos(math.radians(avg_lat))  # meters per degree of longitude
    
    # Calculate differences in degrees
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    # Convert to meters
    dx = dlon * lon_scale
    dy = dlat * lat_scale
    
    # Euclidean distance (Pythagorean theorem)
    return math.sqrt(dx**2 + dy**2)

# checks if the drone's current position is within the buffer zone of any route waypoint, returns Boolean
def is_on_route(lat, lon):
    return any(distance_meters(lat, lon, rlat, rlon) < BUFFER_METERS
               for rlat, rlon in ROUTE)

########################################################### DATA STORAGE ###########################################################

# dictonary to hold most recent drone data, initialise with placeholder values
latest_data = {
    "id": "placeholder text",     # ID
    "lat": 0,               # latitude
    "lon": 0,               # longitude
    "alt": 0,               # altitude
    "rssi": 0,              # Received Signal Strength Indicator
    "on_route": True,       # whether or not the drone is correctly following its course
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
  </div>

  {% if data.on_route %}
  <div class="ok"> Drone is on course</div>
  {% else %}
  <div class="warning">WARNING: Drone has exited route corridor!</div>
  {% endif %}
  
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
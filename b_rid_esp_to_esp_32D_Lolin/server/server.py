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
BUFFER_METERS = 10

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
  <style>
    body { font-family: Arial, sans-serif; padding: 20px; background: #f4f4f4; }
    h1   { color: #333; }
    .card { background: white; padding: 20px; border-radius: 8px; 
            max-width: 400px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); margin-bottom: 15px; }
    .field { margin: 10px 0; font-size: 1.1em; }
    .label { font-weight: bold; color: #555; }
    .warning { background: red; color: white; padding: 15px; 
               border-radius: 8px; margin-bottom: 15px; max-width: 400px;
               font-weight: bold; font-size: 1.1em; }
    .ok { background: green; color: white; padding: 15px;
          border-radius: 8px; margin-bottom: 15px; max-width: 400px;
          font-weight: bold; font-size: 1.1em; }
    #map { height: 400px; max-width: 800px; border-radius: 8px;
           box-shadow: 0 2px 6px rgba(0,0,0,0.1);
           transform: rotate(90deg);
           transform-origin: center center; }
  </style>

  <!-- Leaflet CSS -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"/>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Turf.js/6.5.0/turf.min.js"></script>
</head>
<body>
  <h1>Drone Status</h1>

  <!-- Status banner -->
  {% if data.on_route %}
  <div class="ok"> Drone is on route</div>
  {% else %}
  <div class="warning"> WARNING: Drone has exited route corridor!</div>
  {% endif %}

  <!-- Data card -->
  <div class="card">
    <div class="field"><span class="label">Drone ID:</span> {{ data.id }}</div>
    <div class="field"><span class="label">Latitude:</span> {{ data.lat }}</div>
    <div class="field"><span class="label">Longitude:</span> {{ data.lon }}</div>
    <div class="field"><span class="label">Altitude:</span> {{ data.alt }} m</div>
    <div class="field"><span class="label">RSSI:</span> {{ data.rssi }} dBm</div>
  </div>

  <!-- Map -->
  <div style="overflow: hidden; max-width: 800px;">
    <div id="map"></div>
  </div>

  <!-- Leaflet JS -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
  <script>
    // Route waypoints passed from Flask into JavaScript
    var route = {{ route | tojson }};
    var bufferMeters = {{ buffer }};
    var droneLat = {{ data.lat }};
    var droneLon = {{ data.lon }};
    var onRoute = {{ 'true' if data.on_route else 'false' }};

    // Initialise map centred on the first waypoint
    var map = L.map('map').setView([route[0][0], route[0][1]], 18);

    // Load OpenStreetMap tiles (free, no API key needed)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Convert Leaflet route [lat, lon] to Turf.js format [lon, lat]
    var turfCoordinates = route.map(function(point) { 
        return [point[1], point[0]]; 
    });

    // Create a Turf LineString from the coordinates
    var routeLineString = turf.lineString(turfCoordinates);

    // Generate a mathematical buffer polygon around the line
    var bufferedPolygon = turf.buffer(routeLineString, bufferMeters, { units: 'meters' });

    // Draw the newly combined polygon "tube" onto the Leaflet map
    L.geoJSON(bufferedPolygon, {
      style: {
        color: 'blue',          // The single outer border color
        weight: 1,              // The thickness of the outer border
        fillColor: '#3388ff',
        fillOpacity: 0.15
      }
    }).addTo(map);

    // Draw the center line connecting all the GPS waypoints
    L.polyline(route, {
      color: 'blue',
      weight: 2,             // Thickness of the line
      opacity: 0.8
    }).addTo(map);

    // Draw the drone as a red circle marker
    var droneMarker = L.circleMarker([droneLat, droneLon], {
      radius: 10,
      color: onRoute ? 'red' : 'orange',
      fillColor: onRoute ? 'red' : 'orange',
      fillOpacity: 0.9
    }).addTo(map).bindPopup('Drone: ' + droneLat.toFixed(6) + ', ' + droneLon.toFixed(6));

    // Auto-refresh data every second without reloading the whole page
    setInterval(function() {
      fetch('/data')
        .then(response => response.json())
        .then(data => {
          // Update marker position
          droneMarker.setLatLng([data.lat, data.lon]);
          droneMarker.setStyle({
            color: data.on_route ? 'red' : 'orange',
            fillColor: data.on_route ? 'red' : 'orange'
          });
          droneMarker.setPopupContent('Drone: ' + data.lat.toFixed(6) + ', ' + data.lon.toFixed(6));
        });
    }, 1000);

  </script>
</body>
</html>
"""

########################################################### ROUTES FOR DATA ###########################################################

# first line tells Flask to run the function below when someone requests the root URL
# this renders the dashboard and passes the current latest_data, which fills in the page
@app.route("/")
def index():
    return render_template_string(DASHBOARD, data=latest_data, route=ROUTE, buffer=BUFFER_METERS)

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
        latest_data["on_route"] = is_on_route(data["lat"], data["lon"])
        print("Received:", data, "| On route:", latest_data["on_route"])
    return "OK", 200

########################################################### ENTRY POINT ###########################################################

# [app.run(host="0.0.0.0", port=5000, debug=False)] starts up the Flask web server
# host set to 0.0.0.0 to ensure any device on the same network can access it
# Flask automatically handles incoming POST requests & browser visits accordingly


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
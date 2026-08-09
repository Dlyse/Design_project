#include "esp_wifi.h"
#include "esp_event.h"
#include "nvs_flash.h"
#include "src/opendroneid.h"
#include <WiFi.h>
#include <WebServer.h>

// config for wifi/server stuff
const char* WIFI_SSID  = "rafael";
const char* WIFI_PASS  = "joinhere";
WebServer server(80);

// for data struct
ODID_UAS_Data uas_data;
String latest_json_data = "";      // buffer to hold latest set of data
bool new_data = false;             // flag that triggers upload to server

void handleRoot()
{
  String html = R"rawliteral(
<!DOCTYPE html>
<html>

<head>

<link rel="stylesheet"
href="https://unpkg.com/leaflet/dist/leaflet.css"/>

<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>

<meta charset="utf-8">

<title>ESP32 Drone Receiver</title>

<style>

body{
    font-family:Arial;
    background:#f4f4f4;
    margin:30px;
}

.card{
    background:white;
    padding:20px;
    width:420px;
    border-radius:10px;
    box-shadow:0px 2px 8px rgba(0,0,0,0.2);
}

table{
    width:100%;
}

td{
    padding:6px;
}

.label{
    font-weight:bold;
}

.online{
    color:green;
}

.offline{
    color:red;
}

</style>

</head>

<body>

<div class="card">

<h2>ESP32 Drone Receiver</h2>

<p id="status" class="offline">Waiting for drone...</p>

<div id="map" style="height:400px;"></div>

<table>

<tr><td class="label">Operator ID</td><td id="id">-</td></tr>
<tr><td class="label">Latitude</td><td id="lat">-</td></tr>
<tr><td class="label">Longitude</td><td id="lon">-</td></tr>
<tr><td class="label">Altitude</td><td id="alt">-</td></tr>
<tr><td class="label">RSSI</td><td id="rssi">-</td></tr>

<tr>
    <td class="label">Distance from Route</td>
    <td id="distance">-</td>
</tr>
<tr>
    <td class="label">Status</td>
    <td id="warning">Within Route</td>
</tr>

</table>

</div>

<script>

var flightLog = [];
var lastLogTime = 0;

var map = L.map('map').setView([1.3521,103.8198],16);

L.tileLayer(
'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
{
    attribution:'© OpenStreetMap'
}).addTo(map);

var drone = L.circleMarker(
    [1.3521,103.8198],
    {
        radius: 8,
        color: "red",
        fillColor: "red",
        fillOpacity: 1
    }
).addTo(map);

var droneTrail = [];

var trail = L.polyline([], {
    color: "red",
    weight: 3, 
    opacity: 0.8
}).addTo(map);

// START
const start = [1.3322723838302757, 103.7769543756633];

// END
const end = [1.3328165415986508, 103.77696798328725];

// distance threshold
const THRESHOLD = 5;

var route = L.polyline(
    [start,end],
    {
        color:"blue",
        weight:4
    }
).addTo(map);

L.circleMarker(start,{
    radius:6,
    color:"green",
    fillColor:"green",
    fillOpacity:1
}).addTo(map);

L.circleMarker(end,{
    radius:6,
    color:"red",
    fillColor:"red",
    fillOpacity:1
}).addTo(map);

const tube = L.polyline(
    [start, end],
    {
        color: "green",
        weight: 20,
        opacity: 0.25
    }
).addTo(map);

// ================================
// Distance from route calculation
// ================================

const startLat = start[0];
const startLon = start[1];
            
const endLat = end[0];
const endLon = end[1];

async function updateData()
{
    try
    {
        const response = await fetch("/data");
        const data = await response.json();

        if(data.status)
        {
            document.getElementById("status").innerHTML="Waiting for drone...";            
            document.getElementById("status").className="offline";
            return;
        }

        if(data.lat != 0 && data.lon != 0)
        {
            if (droneTrail.length == 0 || map.distance(droneTrail[droneTrail.length - 1], [data.lat, data.lon]) > 5)
            {
                droneTrail.push([data.lat, data.lon]);
            
                if (droneTrail.length > 50)
                {
                    droneTrail.shift();
                }
            
                trail.setLatLngs(droneTrail);
            }
            drone.setLatLng([data.lat, data.lon]);
            map.setView([data.lat, data.lon], map.getZoom(), {
                animate: true
}           );

            const droneLat = data.lat;
            const droneLon = data.lon;
                        
            // Projection factor
            const dx = endLon - startLon;
            const dy = endLat - startLat;
                        
            let t =
            (
                (droneLon-startLon)*dx
                +
                (droneLat-startLat)*dy
            )
            /
            (
                dx*dx + dy*dy
            );
            
            // Clamp to the route segment
            t = Math.max(0, Math.min(1, t));
                        
            // Closest point on line
            const projLat = startLat + t*dy;
            const projLon = startLon + t*dx;

            const distanceMeters = Math.sqrt(
                Math.pow((droneLat - projLat) * 111320, 2) +
                Math.pow((droneLon - projLon) * 111320 * Math.cos(droneLat * Math.PI / 180), 2)
            );

            const now = Date.now();

            if (now - lastLogTime >= 1000)
            {           
                flightLog.push({
                    time: new Date().toLocaleTimeString(),
                    distance: distanceMeters.toFixed(2)
                });

                console.table(flightLog);
                lastLogTime = now;
            }
            document.getElementById("distance").innerHTML = distanceMeters.toFixed(2) + " m";
            if (distanceMeters > THRESHOLD)
            {
                document.getElementById("warning").innerHTML = "⚠ Outside Allowed Route";
            
                drone.setStyle({
                    color: "orange",
                    fillColor: "orange"
                });
            }
            else
            {
                document.getElementById("warning").innerHTML =
                    "Within Route";
            
                drone.setStyle({
                    color: "red",
                    fillColor: "red"
                });
            }
        }

        document.getElementById("status").innerHTML="Receiving";
        document.getElementById("status").className="online";

        document.getElementById("id").innerHTML=data.id;
        document.getElementById("lat").innerHTML=data.lat;
        document.getElementById("lon").innerHTML=data.lon;
        document.getElementById("alt").innerHTML=data.alt+" m";
        document.getElementById("rssi").innerHTML=data.rssi+" dBm";
    }
    catch(e)
    {
        document.getElementById("status").innerHTML="Disconnected";
        document.getElementById("status").className="offline";
    }
}

setInterval(updateData,500);

updateData();

</script>

</body>

</html>
)rawliteral";

  server.send(200,"text/html",html);
}

void handleData()
{
    if (latest_json_data.length() == 0)
    {
        server.send(200, "application/json",
                    "{\"status\":\"waiting_for_drone\"}");
    }
    else
    {
        server.send(200, "application/json", latest_json_data);
    }
}

// This callback is called by the ESP32's Wi-Fi Driver every time a packet is captured
void sniffer_callback(void* buf, wifi_promiscuous_pkt_type_t type)
{  
  // ignore anything that isn't a Management Packet (which is what B-RID uses)
  if (type != WIFI_PKT_MGMT) return;

  // Cast packet into a format readable by the ESP32.
  // Get payload: actual packet contents.
  // Get len: length/size of packet in bytes (rx_ctrl contains metadata about the reception, such as signal strength, channel, etc.)
  wifi_promiscuous_pkt_t* pkt = (wifi_promiscuous_pkt_t*)buf;
  uint8_t* payload = pkt->payload;
  uint16_t len = pkt->rx_ctrl.sig_len;

  // Beacon frames have subtype 0x08
  // The frame control byte is the first byte of the payload
  // Therefore reject anything that doesn't match
  uint8_t frame_subtype = (payload[0] & 0xF0) >> 4;
  if (frame_subtype != 0x08) return;

  // Search through the packet by looping through every byte for the B-RID OUI fingerprint
  // This sequence of bytes: [0xFA, 0x0B, 0xBC] is the OpenDroneID Organizationally Unique Identifier [OUI]
  // Therefore, if it is found, we have a fully compliant B-RID Wi-Fi Beacon packet
  for (int i = 0; i < len - 3; i++) {
    if (payload[i]   == 0xFA &&
        payload[i+1] == 0x0B &&
        payload[i+2] == 0xBC) {
      
      Serial.println("___B-RID PACKET DETECTED___");

      // The OpenDroneID payload starts 5 bytes after the OUI
      // (OUI = 3 bytes; OUI type = 1 byte; then message pack)
      uint8_t* odid_payload = &payload[i + 5];

      // Clear previous data then decode
      odid_initUasData(&uas_data);
      ODID_MessagePack_encoded* pack = (ODID_MessagePack_encoded*) odid_payload;
      int result = decodeMessagePack(&uas_data, pack);

      if (result == ODID_SUCCESS)
      {

        String opID = String(uas_data.OperatorID.OperatorId);

        if (opID.length() == 0)
          return;
          
        // Build JSON from decoded packets
        latest_json_data  = "{\"id\":\"" + String(uas_data.OperatorID.OperatorId) + "\"";
        latest_json_data += ",\"lat\":"  + String(uas_data.Location.Latitude, 7);
        latest_json_data += ",\"lon\":"  + String(uas_data.Location.Longitude, 7);
        latest_json_data += ",\"alt\":"  + String(uas_data.Location.AltitudeGeo);
        latest_json_data += ",\"rssi\":" + String(pkt->rx_ctrl.rssi) + "}";
        new_data = true;
        Serial.println("Data buffered: " + latest_json_data);
      }
      else
      {
        Serial.println("Decode failed/Non-essential packet");
      }
    }
  }
}

void setup()
{
    Serial.begin(115200);

    odid_initUasData(&uas_data);

    nvs_flash_init();

    WiFi.mode(WIFI_STA);
    WiFi.setSleep(false);

    WiFi.begin(WIFI_SSID, WIFI_PASS);

    Serial.print("Connecting");

    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
    }

    Serial.println();
    Serial.println("Connected!");

    Serial.print("IP: ");
    Serial.println(WiFi.localIP());

    Serial.print("Channel: ");
    Serial.println(WiFi.channel());

    server.on("/", handleRoot);
    server.on("/data", handleData);

    server.begin();
    Serial.print("Open browser: http://");
    Serial.println(WiFi.localIP());

    latest_json_data = "";

    Serial.println("HTTP server started");

    // ---------- TEST ----------
    // DO NOT reinitialise WiFi.
    // just ask for promiscuous mode.

    esp_wifi_set_promiscuous_rx_cb(&sniffer_callback);
    Serial.println("Promiscuous callback registered");
    esp_err_t err = esp_wifi_set_promiscuous(true);

    Serial.print("Promiscuous enable result: ");
    Serial.println(err == ESP_OK ? "OK" : "FAILED");
}

void loop()
{
    server.handleClient();

    static unsigned long lastPrint = 0;

    if (new_data)
    {
        new_data = false;

        Serial.println();
        Serial.println("========== B-RID PACKET ==========");
        Serial.println(latest_json_data);
        Serial.println("==================================");
    }

    if (millis() - lastPrint > 5000)
    {
        lastPrint = millis();

        Serial.print("Connected: ");
        Serial.println(WiFi.status() == WL_CONNECTED);

        Serial.print("IP: ");
        Serial.println(WiFi.localIP());
    }
}

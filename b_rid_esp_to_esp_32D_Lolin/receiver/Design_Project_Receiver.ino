#include "esp_wifi.h"
#include "esp_event.h"
#include "nvs_flash.h"
#include "src/opendroneid.h"

// for data struct
ODID_UAS_Data uas_data;

// This callback is called by the ESP32's Wi-Fi Driver every time a packet is captured
void sniffer_callback(void* buf, wifi_promiscuous_pkt_type_t type) {

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

      // The OpenDroneID payload starts 4 bytes after the OUI
      // (OUI = 3 bytes; OUI type = 1 byte; then message pack)
      uint8_t* odid_payload = &payload[i + 4];

      // Clear previous data then decode
      odid_initUasData(&uas_data);
      ODID_MessagePack_encoded* pack = (ODID_MessagePack_encoded*) odid_payload;
      int result = decodeMessagePack(&uas_data, pack);

      if (result == ODID_SUCCESS)
      {
        // Build JSON from decoded fields
        Serial.print("{\"id\":\"");
        Serial.print(uas_data.BasicID[0].UASID);
        Serial.print("\"");
        Serial.print(",\"lat\":");
        Serial.print(uas_data.Location.Latitude, 7);
        Serial.print(",\"lon\":");
        Serial.print(uas_data.Location.Longitude, 7);
        Serial.print(",\"alt\":");
        Serial.print(uas_data.Location.AltitudeBaro);
        Serial.print(",\"rssi\":");
        Serial.print(pkt->rx_ctrl.rssi);
        Serial.println("}");
      }
      else
      {
        Serial.println("Decode failed");
      }
    }
  }
}

void setup() {
  Serial.begin(115200);

  // struct for data
  odid_initUasData(&uas_data);

  // initialising: Internal ESP32 Flash Memory, Network Interfaces, and Event Loop for background tasks
  nvs_flash_init();
  esp_netif_init();
  esp_event_loop_create_default();

  // Creates default Wi-Fi config and initialise Wi-Fi driver
  // WIFI_INIT_CONFIG_DEFAULT() is a macro that auto-fills the normal settings
  wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
  esp_wifi_init(&cfg);

  // Starts on the Wi-Fi Radio as null, meaning no active connection, just sorta sitting there frfr
  esp_wifi_set_mode(WIFI_MODE_NULL);
  esp_wifi_start();

  // Lock onto only channel 6 (default B-RID Neighbour Awareness Networking [NAN] channel)
  esp_wifi_set_channel(6, WIFI_SECOND_CHAN_NONE);

  // Register callback function: Runs whenever a packet is captured.
  // Also enable promiscuous mode.
  esp_wifi_set_promiscuous_rx_cb(&sniffer_callback);
  esp_wifi_set_promiscuous(true);

  Serial.println("Sniffing started on channel 6...");
}

void loop() {
  // placeholder for serial monitor just so i know the board ain't dead ykyk
  // Serial.println("nothing here cuz no B-RID yet, don't worry");
  delay(1000);
}

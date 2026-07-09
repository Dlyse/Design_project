#include <Arduino.h>

#include "id_open.h"

static ID_OpenDrone          squitter;

static struct UTM_parameters utm_parameters;
static struct UTM_data       utm_data;

void setup() {

  Serial.begin(115200);

  memset(&utm_parameters,0,sizeof(utm_parameters));

  strcpy(utm_parameters.UAS_operator,"UAE-SSRC-1234567");

  utm_parameters.region      = 1;
  utm_parameters.EU_category = 2;

  squitter.init(&utm_parameters);
  
  memset(&utm_data,0,sizeof(utm_data));

  utm_data.base_latitude  = 24.4366767;
  utm_data.base_longitude = 54.6139099;
  utm_data.base_alt_m     = 150.0;

  utm_data.latitude_d  = 24.4366767;
  utm_data.longitude_d = 54.6139099;
  utm_data.alt_msl_m   = 200.0;

  utm_data.satellites = 8;
  utm_data.base_valid = 1;

  return;
}

void loop() {

  squitter.transmit(&utm_data);

  return;
}
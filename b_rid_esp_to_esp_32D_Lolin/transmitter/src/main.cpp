#include <Arduino.h>

#include "id_open.h"

static ID_OpenDrone          squitter;

static struct UTM_parameters utm_parameters;
static struct UTM_data       utm_data;

void setup() {

  Serial.begin(115200);

  memset(&utm_parameters,0,sizeof(utm_parameters));

  strcpy(utm_parameters.UAS_operator,"UAE-SSRC-1234567");

  strcpy(utm_parameters.UAV_id, "TEST-DRONE-0001");
  utm_parameters.UA_type = ODID_UATYPE_HELICOPTER_OR_MULTIROTOR; //ODID_UATYPE_AEROPLANE for planes
  utm_parameters.ID_type = ODID_IDTYPE_SERIAL_NUMBER;

  utm_parameters.region      = 1;
  utm_parameters.EU_category = 2;

  squitter.init(&utm_parameters);
  
  memset(&utm_data,0,sizeof(utm_data));

  utm_data.base_latitude  = 1.342615;
  utm_data.base_longitude = 103.717382;//
  utm_data.base_alt_m     = 10.0;

  utm_data.latitude_d  = 1.342615;
  utm_data.longitude_d = 103.717382;
  utm_data.alt_msl_m   = 30.0; //mean sea lvl

  utm_data.alt_agl_m = 20.0; //heigh above take off point

  utm_data.satellites = 8;
  utm_data.base_valid = 1;

  return;
}

void loop() {
  squitter.transmit(&utm_data);
  return;
}
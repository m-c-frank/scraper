#!/bin/bash

# Get the absolute path of the parent directory of the script
PARENT_DIR=$(readlink -f "$(dirname "$0")/..")

# Run the Docker command with the absolute path
docker run --rm \
  -v "$PARENT_DIR":/workdir \
  eclipse-mosquitto:latest \
  mosquitto_passwd -b -c /workdir/passwordfile $MQTT_USERNAME $MQTT_PASSWORD

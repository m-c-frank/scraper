#!/bin/bash
set -e

# Stop and remove any existing Mosquitto container
echo "Stopping and removing existing Mosquitto container if it exists..."
docker stop mosquitto-dev 2>/dev/null || true
docker rm mosquitto-dev 2>/dev/null || true

# Pull the Mosquitto Docker image (if not present)
echo "Pulling Eclipse Mosquitto Docker image..."
docker pull eclipse-mosquitto:latest

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p ./mosquitto/config ./mosquitto/data ./mosquitto/log

# Create the Mosquitto configuration file if it doesn't exist
if [ ! -f ./mosquitto/config/mosquitto.conf ]; then
    echo "Creating default Mosquitto configuration with authentication..."
    cat <<EOF > ./mosquitto/config/mosquitto.conf
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log

allow_anonymous false
password_file /mosquitto/config/passwordfile

listener 1883

listener 9001
protocol websockets
EOF
fi

# Create the Mosquitto password file using Docker
if [ ! -f ./mosquitto/config/passwordfile ]; then
    echo "Creating Mosquitto password file with credentials 'user:password'..."
    docker run --rm \
        -v "$(pwd)/mosquitto/config:/mosquitto/config" \
        eclipse-mosquitto:latest \
        mosquitto_passwd -b -c /mosquitto/config/passwordfile user password
fi

# Start the Mosquitto container
echo "Starting Mosquitto container..."
docker run -d \
    --name mosquitto-dev \
    -p 1883:1883 \
    -p 9001:9001 \
    -v "$(pwd)/mosquitto/config:/mosquitto/config" \
    -v "$(pwd)/mosquitto/data:/mosquitto/data" \
    -v "$(pwd)/mosquitto/log:/mosquitto/log" \
    eclipse-mosquitto:latest

echo "Mosquitto container setup complete."
echo "Mosquitto MQTT broker is running on ports 1883 (MQTT) and 9001 (WebSockets)."

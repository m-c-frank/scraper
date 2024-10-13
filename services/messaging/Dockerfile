FROM eclipse-mosquitto:latest

# Copy configuration and password files
COPY mosquitto.conf /mosquitto/config/mosquitto.conf
COPY passwordfile /mosquitto/config/passwordfile

# Set appropriate permissions
RUN chown -R mosquitto:mosquitto /mosquitto/config

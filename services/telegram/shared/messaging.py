import paho.mqtt.client as mqtt
import os
import logging

class Messaging:
    def __init__(self):
        # Configure logging
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        self.broker = os.getenv("MQTT_BROKER", "localhost")
        self.username = os.getenv("MQTT_USERNAME", "user")
        self.password = os.getenv("MQTT_PASSWORD", "password")
        self.port = int(os.getenv("MQTT_PORT", 1883))
        
        # Initialize the MQTT client
        self.client = mqtt.Client(reconnect_on_failure=True)
        self.client.username_pw_set(self.username, self.password)

        # Connect to the broker
        self.connect()

    def connect(self):
        """Connect to the MQTT broker and start the loop."""
        try:
            self.client.connect(self.broker, self.port)
            self.client.loop_start()  # Keep the loop running
            self.logger.info("Connected to the MQTT broker")
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")

    def publish(self, topic, message, qos=0):
        """Publish a message to a specific MQTT topic."""
        try:
            result = self.client.publish(topic, message, qos=qos)
            status = result.rc
            if status == mqtt.MQTT_ERR_SUCCESS:
                self.logger.info(f"Sent `{message}` to topic `{topic}`")
            else:
                self.logger.error(f"Failed to send message to topic {topic}, status {status}")
        except Exception as e:
            self.logger.error(f"Error during publishing: {e}")

    def disconnect(self):
        """Disconnect from the MQTT broker."""
        try:
            self.client.loop_stop()  # Stop the loop
            self.client.disconnect()  # Disconnect from the broker
            self.logger.info("Disconnected from the MQTT broker")
        except Exception as e:
            self.logger.error(f"Error during disconnection: {e}")

    def __del__(self):
        self.disconnect()  # Ensure proper cleanup

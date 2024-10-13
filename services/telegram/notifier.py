import os
import requests
import logging
import time
from shared.messaging import Messaging
from shared.models import Item
from shared.utils import SessionLocal

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Telegram bot settings from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
logger.debug(f"Telegram API URL set to {TELEGRAM_API_URL}")

def send_telegram_message(item: Item):
    """Send a message with item details to a Telegram chat."""
    logger.info(f"Preparing to send Telegram message for item: {item.title}")
    message = (
        f"<b>Title:</b> {item.title}\n"
        f"<b>Location:</b> {item.location}\n"
        f"<b>Distance:</b> {item.distance:.1f} km\n"
        f"<b>Date:</b> {item.date.strftime('%d.%m.%Y %H:%M')}\n"
        f"<a href='{item.link}'>View Listing</a>"
    )
    try:
        response = requests.post(
            TELEGRAM_API_URL,
            data={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        )
        if response.status_code != 200:
            logger.error(f"Failed to send Telegram message: {response.status_code}, {response.text}")
        else:
            logger.info(f"Sent Telegram message for item: {item.title}")
    except requests.RequestException as e:
        logger.error(f"Error sending Telegram message: {e}")

def on_message(client, userdata, msg):
    """Callback function for when a message is received on the MQTT topic."""
    logger.info(f"Received message on topic `{msg.topic}` with payload `{msg.payload.decode('utf-8')}`")
    try:
        item_id = int(msg.payload.decode("utf-8"))
        logger.info(f"Received new item ID: {item_id}")
        
        session = SessionLocal()
        item = session.query(Item).get(item_id)
        if item:
            logger.info(f"Item found in database: {item.title}")
            send_telegram_message(item)
        else:
            logger.warning(f"Item with ID {item_id} not found in the database.")
        session.close()
        logger.debug("Database session closed.")
    except Exception as e:
        logger.error(f"Error processing message: {e}")

def on_subscribe(client, userdata, mid, granted_qos):
    logger.info(f"Subscribed to topic with message ID {mid} and QoS {granted_qos}")

def on_disconnect(client, userdata, rc):
    """Handle disconnection and attempt reconnection."""
    if rc != 0:
        logger.warning(f"Unexpected disconnection (result code {rc}). Attempting to reconnect...")
        attempts = 0
        while True:
            try:
                client.reconnect()
                logger.info("Reconnected to the broker.")
                break
            except Exception as e:
                attempts += 1
                logger.error(f"Reconnect attempt {attempts} failed: {e}")
                time.sleep(5)  # Wait before retrying
    else:
        logger.info("Disconnected gracefully.")

if __name__ == "__main__":
    logger.info("Starting the notifier service.")
    
    messaging = Messaging()  # Use the updated Messaging class

    # Subscribe to the MQTT topic
    MQTT_TOPIC = os.getenv("MQTT_TOPIC", "scraper")
    messaging.client.on_message = on_message
    messaging.client.on_subscribe = on_subscribe
    messaging.client.on_disconnect = on_disconnect
    messaging.client.subscribe(MQTT_TOPIC)
    logger.info(f"Subscribed to topic `{MQTT_TOPIC}` and waiting for messages.")
    
    # Keep the MQTT loop running
    messaging.client.loop_forever()

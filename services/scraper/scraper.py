import asyncio
import os
import requests
import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, ValidationError, field_validator

from shared.utils import SessionLocal  # Import SessionLocal from utils
from shared.models import Item  # Import models from models.py
from shared.messaging import Messaging  # Import Messaging

# Constants
URL_BASE = "https://www.kleinanzeigen.de/"
SCRAPE_URL = f"{URL_BASE}s-immobilien/augsburg/anzeige:angebote/c195l7518r20"

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Pydantic model for validation
class BaseItem(BaseModel):
    title: str
    location: str
    distance_km: float = Field(alias="distance_km")
    date: datetime
    image: Optional[str] = None
    link: str

    @field_validator('distance_km', mode='before')
    def validate_distance(cls, value):
        """Validate and convert the distance."""
        if isinstance(value, str):
            return float(value.replace("ca. ", "").replace(" km", "").strip())
        return value

    @field_validator('date', mode='before')
    def validate_date(cls, value):
        """Convert date string to a UTC datetime object."""
        if isinstance(value, str):
            if "Heute" in value:
                _, time_str = value.split(",", 1)
                current_day = datetime.now(timezone.utc).date()
                return datetime.combine(
                    current_day, datetime.strptime(time_str.strip(), "%H:%M").time()
                )
            elif "Gestern" in value:
                _, time_str = value.split(",", 1)
                yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
                return datetime.combine(
                    yesterday, datetime.strptime(time_str.strip(), "%H:%M").time()
                )
            try:
                return datetime.strptime(value, "%d.%m.%Y")
            except ValueError:
                return datetime(1970, 1, 1)  # Default to epoch if invalid
        return value

    class Config:
        populate_by_name = True  # Updated configuration key

# Configuration class for the scraper
class ScraperConfig:
    def __init__(self, topic: str, wait_duration: int):
        self.topic = topic
        self.wait_duration = wait_duration

# Main Scraper class
class Scraper:
    def __init__(self, config: ScraperConfig, db_session):
        self.config = config
        self.messaging = Messaging()  # Initialize Messaging class for MQTT
        self.db_session = db_session

    async def scrape_page(self, page, url: str) -> str:
        """Navigate to the page and return its HTML content."""
        await page.goto(url)
        return await page.content()

    def parse_item(self, html_main: str, html_img: str) -> Optional[BaseItem]:
        """Parse HTML and return a BaseItem model."""
        soup_main = BeautifulSoup(html_main, "html.parser")

        # Title and link extraction
        link_span = soup_main.find("span", class_="ellipsis")
        link_a = soup_main.find("a", class_="ellipsis")
        title, link = None, None
        if link_span and link_span.get_text(strip=True):
            title = link_span.get_text(strip=True)
            link = link_span.get("data-url", "").strip()
        elif link_a and link_a.get_text(strip=True):
            title = link_a.get_text(strip=True)
            link = link_a.get("href", "").strip()

        if not link:
            logger.warning("No link found for an item; skipping.")
            return None
        
        if not link.startswith("http"):
            link = URL_BASE + link

        # Location and distance extraction
        location_div = soup_main.find("div", class_="aditem-main--top--left")
        if location_div:
            location_text = location_div.get_text(strip=True)
            if "(" in location_text:
                location, distance = location_text.split("(", maxsplit=1)
                distance = distance.replace(")", "").strip()
            else:
                location, distance = location_text, "0 km"
        else:
            location, distance = "Unknown", "0 km"

        # Date extraction
        date_div = soup_main.find("div", class_="aditem-main--top--right")
        date_str = date_div.get_text(strip=True) if date_div else "01.01.1970"

        if date_str == "01.01.1970":
            logger.warning("No date found for an item; skipping.")
            return None

        # Image extraction
        soup_img = BeautifulSoup(html_img, "html.parser")
        img_elem = soup_img.find("img")
        img_save = ""
        if img_elem and img_elem.get("src"):
            img_url = img_elem["src"]
            try:
                response = requests.get(img_url)
                if response.status_code == 200:
                    img_save = base64.b64encode(response.content).decode("utf-8")
            except requests.RequestException as e:
                logger.error(f"Failed to download image: {e}")

        # Create BaseItem using Pydantic
        try:
            item = BaseItem(
                title=title,
                location=location.strip(),
                distance_km=distance,
                date=date_str,
                image=img_save,
                link=link,
            )
            return item
        except ValidationError as e:
            logger.error(f"Pydantic Validation Error: {e}")
            return None

    async def scrape_items(self, page, url: str) -> list:
        """Scrape items from the given URL."""
        page_content = await self.scrape_page(page, url)
        soup = BeautifulSoup(page_content, "html.parser")
        aditem_mains = soup.find_all("div", class_="aditem-main")
        aditem_imgs = soup.find_all("div", class_="aditem-image")

        items = []
        for ad_main, ad_img in zip(aditem_mains, aditem_imgs):
            item = self.parse_item(str(ad_main), str(ad_img))
            if item:
                items.append(item)
        return sorted(items, key=lambda item: item.date, reverse=True)

    def save_item_to_db(self, item: BaseItem):
        """Save the item to the database if not already present."""
        existing_item = self.db_session.query(Item).filter_by(link=item.link).first()
        if existing_item:
            logger.info(f"Item already exists in DB: {item.title}")
        else:
            # Create a new Item instance
            new_item = Item(
                title=item.title,
                location=item.location,
                distance=item.distance_km,
                date=item.date,
                image=item.image,
                link=item.link,
            )
            self.db_session.add(new_item)
            self.db_session.commit()
            # Publish the new item ID to MQTT
            self.messaging.publish(
                topic=self.config.topic,
                message=str(new_item.id)  # Ensure the message is a string
            )
            logger.info(f"Saved new item to DB and published ID: {new_item.id}")

    async def scrape(self, url: str):
        """Main scraping logic."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            items = await self.scrape_items(page, url)
            for item in items:
                self.save_item_to_db(item)

            await browser.close()

async def countdown(seconds: int):
    """Log countdown for the given number of seconds."""
    logger.info(f"Next scrape in {seconds} seconds")
    while seconds:
        await asyncio.sleep(1)
        seconds -= 1

async def scheduled_scrape(scraper: Scraper, url: str, interval: int):
    """Run the scraper at regular intervals."""
    while True:
        logger.info(f"Scraping started at {datetime.now()}")
        try:
            await scraper.scrape(url)
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
        logger.info(f"Scraping finished at {datetime.now()}")
        await countdown(interval)

async def main():
    # Initialize database session
    db_session = SessionLocal()

    # Configuration for the scraper
    topic = os.getenv("MQTT_TOPIC")
    wait_duration = int(os.getenv("SCRAPE_INTERVAL", 60))  # Default to 60 seconds

    config = ScraperConfig(
        topic=topic,
        wait_duration=wait_duration,
    )

    scraper = Scraper(config, db_session)
    url = SCRAPE_URL

    # Set the interval in seconds
    interval = wait_duration  # For example, run the scraping every `wait_duration` seconds
    await scheduled_scrape(scraper, url, interval)

    # Close the database session when done
    db_session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scraper stopped manually.")

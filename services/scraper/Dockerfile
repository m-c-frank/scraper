FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir playwright

# Install playwright browsers
RUN playwright install --with-deps chromium

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the service code
COPY scraper.py .

# Copy shared code
COPY shared ./shared

CMD ["python", "scraper.py"]

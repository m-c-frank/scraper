# scraper

## overview

using playwright to scrape urls
notifying the user via telegram
and internal messaging service through mqtt
and storing items in postgres

## directory structure

```sh
project_root/
├── scripts/
│   ├── build.sh
│   └── setup_dev_mosquitto.sh
├── services/
│   ├── messaging/
│   │   ├── scripts/
│   │   │   └── make_password.sh
│   │   ├── Dockerfile
│   │   └── mosquitto.conf
│   ├── scraper/
│   │   ├── shared/
│   │   │   ├── messaging.py
│   │   │   ├── utils.py
│   │   │   └── models.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── scraper.py
│   ├── telegram/
│   │   ├── shared/
│   │   │   ├── messaging.py
│   │   │   ├── utils.py
│   │   │   └── models.py
│   │   ├── Dockerfile
│   │   ├── notifier.py
│   │   └── requirements.txt
│   ├── add-your-service-here/
│   │   ├── Dockerfile
│   │   └── other_service.py
│   └── ... (additional services)
│   └── init.sql
├── .env
├── docker-compose.yml
└── README.md
```

## setup

### requirements

- Docker
- Docker Compose

### setup

1. clone repo

```sh
git clone https://github.com/m-c-frank/scraper
cd scraper
```

2. setup .env

copy the example `.env` file and enter your telegram bot creds

```sh
cp .env.example .env
```

3. build and run

run the `build.sh` script

```sh
bash scripts/build.sh
docker compose up -d
```

## services

### scraper

- scrapes the main page and stores new items in the database.
- notifies other services using messaging service -> sends id to topic

### telegram

- gets notified via mqtt
- gets item via id thats broadcast in topic
- sends item to telegram chat

### messaging

- just mosquitto
- a mqtt broker

### database

- just postgresql

## contributing

contributions are welcome!
submit a pull request or open an issue

## license

This project is licensed under the MIT License.

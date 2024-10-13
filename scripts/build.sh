#!/bin/bash

# Get the absolute path of the parent directory of the script
PROJECT_ROOT=$(readlink -f "$(dirname "$0")/..")

## load .env from  project_root
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(cat "$PROJECT_ROOT/.env" | grep -v '#' | awk '/=/ {print $1}')
else
    echo "Error: .env file not found"
    exit 1
fi

# run project_root/services/messaging/scripts/make_password.sh
bash "$PROJECT_ROOT/services/messaging/scripts/make_password.sh"

# check if services/messagging/passwordfile exists
if [ ! -f "$PROJECT_ROOT/services/messaging/passwordfile" ]; then
    echo "Error: services/messaging/passwordfile not found"
    exit 1
else
    echo "services/messaging/passwordfile created successfully at $PROJECT_ROOT/services/messaging/passwordfile"
fi

docker compose build --no-cache
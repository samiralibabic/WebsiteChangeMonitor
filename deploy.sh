#!/bin/bash

SECRET_KEY="$1"
DATABASE_URL="$2"
STRIPE_SECRET_KEY="$3"

REPO_URL="https://github.com/samiralibabic/WebsiteChangeMonitor.git"  # Replace with your actual repository URL

if [ ! -d /home/website-monitor ]; then
    mkdir -p /home/website-monitor
fi
cd /home/website-monitor || exit

if [ ! -d .git ]; then
    echo "Cloning repository for the first time..."
    git clone "$REPO_URL" . || { echo "Git clone failed"; exit 1; }
else
    echo "Pulling latest changes from repository..."
    git pull origin main || { echo "Git pull failed"; exit 1; }
fi

docker-compose build || { echo "Build failed"; exit 1; }
docker-compose down

export SECRET_KEY="$SECRET_KEY"
export DATABASE_URL="$DATABASE_URL"
export STRIPE_SECRET_KEY="$STRIPE_SECRET_KEY"

docker-compose up -d || { echo "Failed to start website-monitor"; exit 1; }

echo "Deployment complete for website-monitor"

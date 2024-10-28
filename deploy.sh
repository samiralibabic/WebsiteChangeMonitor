#!/bin/bash

SECRET_KEY="$1"
DATABASE_URL="$2"
STRIPE_SECRET_KEY="$3"

cd /path/to/website-monitor || exit

git pull origin main || { echo "Git pull failed"; exit 1; }

docker-compose build || { echo "Build failed"; exit 1; }

docker-compose down

docker-compose up -d \
  -e SECRET_KEY="$SECRET_KEY" \
  -e DATABASE_URL="$DATABASE_URL" \
  -e STRIPE_SECRET_KEY="$STRIPE_SECRET_KEY" || { echo "Failed to start website-monitor"; exit 1; }

echo "Deployment complete for website-monitor"
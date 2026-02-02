#!/bin/bash

# Setup cron job
# Note: Docker environments don't persist env vars to cron sessions automatically.
# We redirect output to /var/log/cron.log for debugging.

echo "Installing cron job..."
# Runs every hour at 08h-20h
# Ensure we use absolute paths in docker
echo "0 8-20 * * * cd /app && /usr/local/bin/python run_campaigns.py >> /var/log/cron.log 2>&1" > /etc/cron.d/campaign-cron

# Give execution rights on the cron job
chmod 0644 /etc/cron.d/campaign-cron

# Apply cron job
crontab /etc/cron.d/campaign-cron

# Create log file
touch /var/log/cron.log

# Start cron in background
cron

echo "🚀 Crontab installed. Starting Web Server..."

# Start Gunicorn
# -w 1: Single worker (since we use SQLite and it's an MVP)
# -b 0.0.0.0:5000: Bind to all interfaces
# --timeout 120: Increase timeout for long requests if any
exec gunicorn -w 1 -b 0.0.0.0:5000 --timeout 120 web.app:app

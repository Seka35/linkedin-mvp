FROM python:3.12-slim

# Install system dependencies
# cron: for scheduling tasks
# curl: general utility
# build-essential: for compiling python packages if needed
RUN apt-get update && apt-get install -y \
    cron \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install Playwright + Browsers
# We install playwright first to leverage caching if requirements.txt changes often
RUN pip install --no-cache-dir playwright
RUN playwright install --with-deps chromium

# Copy requirements and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Expose port (Flask default)
EXPOSE 5000

# Use custom entrypoint to run Cron + App
ENTRYPOINT ["./entrypoint.sh"]

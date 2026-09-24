FROM python:3.11-slim

WORKDIR /app

# Chromium + driver + fonts needed for headless scraping
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    postgresql-client \
    curl \
    fonts-liberation \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# Point undetected-chromedriver at the distro-packaged browser
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# /app/backend is mounted read-only at runtime so scraper can import app.models
ENV PYTHONPATH=/app:/app/backend

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

CMD ["python", "server.py"]

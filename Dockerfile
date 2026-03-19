FROM python:3.12-slim

WORKDIR /app

# Install build tools needed for pyswisseph (kerykeion dependency)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure seed data is in image (seed_from_csv reads from data/new/)
RUN test -d data/new && test -f "data/new/Astro Data - signs.csv" || (echo "ERROR: data/new missing - seed CSVs required" && exit 1)

RUN chmod +x start.sh

CMD ["./start.sh"]

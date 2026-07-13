FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x scripts/entrypoint.sh scripts/free_boot.sh \
    && mkdir -p storage/uploads

EXPOSE 8000

# free_boot: pgvector → migrate → seed → gunicorn (respects $PORT for Render)
CMD ["bash", "scripts/free_boot.sh"]

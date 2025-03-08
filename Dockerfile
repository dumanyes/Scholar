FROM python:3.9-slim

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y libffi-dev libssl-dev zlib1g-dev libjpeg-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose a default port (Railway will map it automatically).
EXPOSE 8000

# Use a shell command so that $PORT expands to the actual environment variable.
CMD ["sh", "-c", "gunicorn user_management.asgi:application -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000}"]

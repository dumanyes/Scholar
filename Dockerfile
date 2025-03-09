FROM python:3.9-slim

WORKDIR /app

# Install system dependencies needed by Pillow, etc.
RUN apt-get update && apt-get install -y libffi-dev libssl-dev zlib1g-dev libjpeg-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt


COPY . .

EXPOSE 8080

# Use a shell so environment variables like $PORT can expand.
# If PORT isn't set, fallback to 8080.
CMD ["sh", "-c", "gunicorn user_management.asgi:application -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8080}"]

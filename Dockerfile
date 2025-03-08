FROM python:3.9-slim

# Install system dependencies needed for building packages like Pillow and cffi.
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    zlib1g-dev \
    libjpeg-dev \
    libfreetype6-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies.
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of your project.
COPY . /app/

# Expose the port defined by Railway.
CMD ["gunicorn", "user_management.asgi:application", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:$PORT"]

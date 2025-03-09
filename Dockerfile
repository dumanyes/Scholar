FROM python:3.9

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    libomp-dev \
    swig \
    libfaiss-dev

# Create a symlink so that the FAISS headers can be found in /usr/local/include/faiss
RUN mkdir -p /usr/local/include && ln -s /usr/include/faiss /usr/local/include/faiss

COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /app/

EXPOSE 8080

CMD ["gunicorn", "user_management.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:$PORT", "--timeout", "120"]

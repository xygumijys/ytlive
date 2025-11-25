FROM python:3.11-slim

# Install ffmpeg and procps (for ps command if needed)
RUN apt-get update && \
    apt-get install -y ffmpeg procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

COPY . .

# Create storage directory
RUN mkdir -p storage

CMD ["python", "bot.py"]

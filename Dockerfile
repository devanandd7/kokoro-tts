# Base image
FROM python:3.11-slim

# Install system dependencies (espeak-ng is REQUIRED for Kokoro TTS)
RUN apt-get update && apt-get install -y \
    espeak-ng \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirement list and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Expose Render's default port 
EXPOSE 8000

# Start Uvicorn, mapping the dynamic $PORT provided by Render
CMD sh -c "uvicorn local_server:app --host 0.0.0.0 --port ${PORT:-8000}"

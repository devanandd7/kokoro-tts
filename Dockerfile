# Base image (using slim to save RAM/Space)
FROM python:3.11-slim

# Install system dependencies (espeak-ng is REQUIRED for Kokoro TTS)
RUN apt-get update && apt-get install -y \
    espeak-ng \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (leverages Docker cache)
COPY requirements.txt .

# Install CPU-specific torch and other dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port (Render sets $PORT env automatically)
EXPOSE 8000

# Optimized Uvicorn settings for low-memory environments
CMD uvicorn local_server:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --timeout-keep-alive 120

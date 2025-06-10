FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install system dependencies for moviepy and OpenCV
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p uploads generated temp

COPY . .

EXPOSE 8000

CMD ["uvicorn", "server1:app", "--host", "0.0.0.0", "--port", "8000"]

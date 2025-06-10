FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and build tools
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    build-essential \
    imagemagick \
    libmagickwand-dev \
    && rm -rf /var/lib/apt/lists/*

# Configure ImageMagick policy to allow PDF operations
RUN sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/' /etc/ImageMagick-6/policy.xml

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p uploads generated temp

COPY . .

EXPOSE 8000

CMD ["uvicorn", "server1:app", "--host", "0.0.0.0", "--port", "8000"]

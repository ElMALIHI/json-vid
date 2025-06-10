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
    fonts-dejavu \
    fonts-liberation \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Configure ImageMagick policy
RUN for policy_file in /etc/ImageMagick*/policy.xml; do \
        if [ -f "$policy_file" ]; then \
            # Allow text operations
            sed -i 's/rights="none" pattern="[A-Z]*"/rights="read|write" pattern="[A-Z]*"/g' "$policy_file" && \
            # Allow path operations
            sed -i 's/<policy domain="path" rights="none" pattern="@\*"/><policy domain="path" rights="read|write" pattern="@*"/' "$policy_file" && \
            # Allow memory operations
            sed -i 's/<policy domain="resource" name="memory" value="[0-9]*"\/>//' "$policy_file" && \
            echo "Updated policy file: $policy_file"; \
        fi \
    done

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p uploads generated temp

COPY . .

EXPOSE 8000

CMD ["uvicorn", "server1:app", "--host", "0.0.0.0", "--port", "8000"]

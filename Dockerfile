FROM python:3.10-slim

# Prevent prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (Chrome, OpenVPN, and utilities)
RUN apt-get update && apt-get install -y \
    sudo \
    wget \
    curl \
    unzip \
    xvfb \
    openvpn \
    iptables \
    iproute2 \
    chromium \
    chromium-driver \
    ffmpeg \
    procps \
    psmisc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies first (better Docker caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the Whisper AI model to speed up the container's first run
RUN python3 -c "try:\n from faster_whisper import WhisperModel\n WhisperModel('tiny', device='cpu', compute_type='int8')\nexcept:\n pass"

# Copy the rest of the project files
COPY . .

# Ensure scripts are executable
RUN chmod +x *.sh

# Default command: run main.py with VPN rotation and headless mode
ENTRYPOINT ["python3", "main.py", "-v", "--headless"]

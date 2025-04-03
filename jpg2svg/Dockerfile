# Use Python slim image as base
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    potrace \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the converter script
COPY jpg_to_svg_converter.py .

# Set the entrypoint
ENTRYPOINT ["python", "jpg_to_svg_converter.py"] 
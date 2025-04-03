FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for Pillow
RUN apt-get update && apt-get install -y \
    libfreetype6-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy required files
COPY template_generator.py /app/
COPY korean_reference_chars.py /app/
COPY NanumGothic.ttf /app/

# Install Python dependencies
RUN pip install --no-cache-dir pillow

# Create output directory
RUN mkdir -p /app/output_templates

# Run the template generator
CMD ["python", "template_generator.py"] 
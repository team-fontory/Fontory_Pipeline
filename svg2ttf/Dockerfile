FROM ubuntu:22.04

# Set UTF-8 Locale and Python IO Encoding
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONIOENCODING=UTF-8

# Basic setup and FontForge installation
RUN apt-get update && apt-get install -y --no-install-recommends \
    fontforge \
    python3 \
    python3-pip \
    python3-fontforge \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the conversion script
COPY svg_to_ttf_converter.py /app/

# Create directories for input and output
RUN mkdir -p /app/input_svg /app/output_ttf

# Ensure script is executable
RUN chmod +x /app/svg_to_ttf_converter.py

# Set the entrypoint to run the FontForge script
# ENTRYPOINT ["fontforge", "-script", "/app/svg_to_ttf_converter.py"]
ENTRYPOINT ["python3", "/app/svg_to_ttf_converter.py"]
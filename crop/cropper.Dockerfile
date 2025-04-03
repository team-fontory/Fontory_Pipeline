FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir pillow numpy

# Copy the cropper script itself
# Path is relative to the build context (PROJECT_ROOT)
COPY crop/glyph_cropper.py /app/

# Copy shared resources from the new location
COPY ../resource/korean_reference_chars.py /app/
COPY ../resource/NanumGothic.ttf /app/

# Copy the template generator (needed to load settings)
COPY ../make_template/template_generator.py /app/make_template/template_generator.py

# Create necessary directories inside the container
RUN mkdir -p /app/written \
             /app/cropped \
             /app/debug_crops \
             /app/make_template # Ensure make_template directory exists for the import

# Ensure the script is executable
RUN chmod +x /app/glyph_cropper.py

# Default command (optional, can be overridden by docker run)
# CMD ["/app/glyph_cropper.py"] 
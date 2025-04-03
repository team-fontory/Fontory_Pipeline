FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir pillow numpy

# Copy the template generator script
COPY make_template/template_generator.py /app/

# Copy shared resources needed by the generator
# These paths are relative to the build context (project root)
COPY resource/korean_reference_chars.py /app/resource/
COPY resource/NanumGothic.ttf /app/resource/

# Create the resource directory in the container
# It might be created by the COPY above, but this ensures it
RUN mkdir -p /app/resource

# Create the default output directory within the container
# The volume mount will overlay this
RUN mkdir -p /app/output_templates 

# Default command to run the generator
CMD ["python", "/app/template_generator.py"] 
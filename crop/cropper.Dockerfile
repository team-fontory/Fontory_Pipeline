FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir pillow numpy

COPY crop/glyph_cropper.py /app/

COPY ../resource/korean_reference_chars.py /app/
COPY ../resource/NanumGothic.ttf /app/

COPY ../make_template/template_generator.py /app/make_template/template_generator.py

RUN mkdir -p /app/written \
             /app/cropped \
             /app/debug_crops \
             /app/make_template # Ensure make_template directory exists for the import

RUN chmod +x /app/glyph_cropper.py

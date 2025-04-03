FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libfreetype6-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

COPY template_generator.py /app/
COPY korean_reference_chars.py /app/
COPY NanumGothic.ttf /app/

RUN pip install --no-cache-dir pillow

RUN mkdir -p /app/output_templates

CMD ["python", "template_generator.py"] 
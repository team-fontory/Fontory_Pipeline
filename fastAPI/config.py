import os
from dotenv import load_dotenv
from logging_loki import LokiHandler

load_dotenv()  # .env 파일 로드

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_DIR = os.path.join(PROJECT_ROOT, "log")
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")
WRITTEN_DIR = os.path.join(PROJECT_ROOT, "written")
RESULT_DIR = os.path.join(PROJECT_ROOT, "result")

AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
QUEUE_URL = os.getenv("QUEUE_URL")
FONT_BUCKET_NAME = os.getenv("FONT_BUCKET_NAME")
FONT_CREATE_LOG_BUCKET_NAME = os.getenv("FONT_CREATE_LOG_BUCKET_NAME")

MEMBER_ID_KEY = "memberId"
AUTHOR_KEY = "author"
FONT_ID_KEY = "fontId"
FONT_NAME_KEY = "fontName"
TEMPLATE_URL_KEY = "templateURL"
REQUEST_UUID_KEY = "requestUUID"

LOKI_URL = "http://localhost:3100/loki/api/v1/push"

# LokiHandler 생성 (필요한 옵션 설정)
LOKI_HANDLER = LokiHandler(
    url=LOKI_URL,
    tags={"application": "fastapi"},
    version="1"
)
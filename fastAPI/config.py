import os
from dotenv import load_dotenv

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
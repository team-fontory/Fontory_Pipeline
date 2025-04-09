import os
import uvicorn
import logging
from fastAPI.config import RESULT_DIR, LOG_DIR, PROJECT_ROOT, LOKI_HANDLER
from fastAPI.test_api import router as font_router
from fastAPI.prometheus_loki.prometheus_api import router as metrics_router
from fastAPI.sqs_utils import start_sqs_polling
from contextlib import asynccontextmanager
from fastapi import FastAPI

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

loki_url = "http://localhost:3100/loki/api/v1/push"

class MetricsFilter(logging.Filter):
    def filter(self, record):
        # 로그 메시지에 "/metrics"가 포함된 경우 필터링(제외)합니다.
        if "/metrics" in record.getMessage():
            return False
        return True
    
logger = logging.getLogger()
logger.addHandler(LOKI_HANDLER)
logger.addFilter(MetricsFilter())

logging.getLogger("uvicorn.access").addFilter(MetricsFilter())

@asynccontextmanager
async def lifespan(app: FastAPI):
    # SQS 폴링 스레드를 시작
    start_sqs_polling()
    yield  # 앱이 실행되는 동안 유지
    
app = FastAPI(lifespan=lifespan)
app.include_router(font_router)
app.include_router(metrics_router)

if __name__ == "__main__":
    # 필요한 디렉토리 생성
    for subdir in ["1_cropped", "2_inference", "3_svg", "4_fonts"]:
        os.makedirs(os.path.join(RESULT_DIR, subdir), exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(os.path.join(PROJECT_ROOT, "written"), exist_ok=True)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
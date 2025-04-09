from fastapi import APIRouter
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

router = APIRouter()

@router.get("/metrics")
def metrics():
    data = generate_latest()  # 모든 메트릭을 bytes로 반환
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
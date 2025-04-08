from fastAPI.script_utils import cleanup_intermediate_results
from fastAPI.pipeline_runner import run_font_pipeline
from fastAPI.logger_utils import setup_logger
from fastapi import HTTPException, APIRouter
from fastAPI.models import FontRequest

router = APIRouter()

# for test
@router.post("/font")
async def create_font(request: FontRequest):
    font_name = request.font_name
    member_id = request.member_id
    font_id = request.font_id
    request_id = request.request_uuid
    author = request.author
    
    logger, log_file = setup_logger(request_id, member_id, font_id, font_name)
    logger.info(f"폰트 생성 요청 수신: {font_name})")
    try:
        result_ttf_path, result_woff_path = run_font_pipeline(font_name, request_id, logger)
        logger.info(f"폰트 '{font_name}' 생성 성공")
        
        return {
            "message": f"폰트 '{font_name}' 생성 완료",
            "request_id": request_id,
            "log_file": log_file,
            "output_ttf": result_ttf_path,
            "output_woff": result_woff_path,
        }
    except Exception as e:
        error_message = f"폰트 '{font_name}' 생성 중 오류 발생: {str(e)}"
        logger.error(error_message, exc_info=True)
        raise HTTPException(status_code=500, detail=error_message)
    finally:
        cleanup_intermediate_results(font_name, logger)
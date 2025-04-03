import os
import logging
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import subprocess
import time
import shlex
import shutil

# --- Configuration ---
# 호스트 환경 기준 경로
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(PROJECT_ROOT, "log")
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")
RESULT_DIR = os.path.join(PROJECT_ROOT, "result")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# --- 커스텀 로깅 포매터 ---
class RequestIdFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%', request_id=''):
        super().__init__(fmt, datefmt, style)
        self.request_id = request_id
        
    def format(self, record):
        # 기본 포맷팅 진행
        formatted = super().format(record)
        # 타임스탬프와 로그 레벨 사이에 UUID 삽입
        parts = formatted.split(' - ', 1)
        if len(parts) > 1:
            return f"{parts[0]} - [{self.request_id}] - {parts[1]}"
        return formatted

# --- Pydantic Models ---
class FontRequest(BaseModel):
    font_name: str

# --- FastAPI App ---
app = FastAPI()

# --- Helper Function for Logging ---
def setup_logger(request_id: str, font_name: str):
    # 현재 시간 및 로그 파일명 생성 (형식: [시간][UUID 앞 6자][fontname].log)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_id = request_id[:6]  # UUID의 앞 6자만 사용
    log_filename = f"{timestamp}_{short_id}_{font_name}.log"
    log_file_path = os.path.join(LOG_DIR, log_filename)
    
    # 로거 설정
    logger = logging.getLogger(request_id)  # UUID를 로거 이름으로 사용
    logger.setLevel(logging.INFO)
    
    # 핸들러가 이미 추가되어 있으면 초기화 (새 요청 시마다 재설정)
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # 파일 핸들러 설정
    file_handler = logging.FileHandler(log_file_path)
    file_formatter = RequestIdFormatter('%(asctime)s - %(levelname)s - %(message)s', 
                                        request_id=short_id)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler()
    console_formatter = RequestIdFormatter('%(asctime)s - %(levelname)s - %(message)s', 
                                          request_id=short_id)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 로그 파일 경로 반환
    return logger, log_file_path

# --- Script Execution Function ---
def run_script(script_path, args, logger, step_name):
    try:
        cmd = [script_path]
        if args:
            cmd.extend(args)
        
        cmd_str = ' '.join(shlex.quote(arg) for arg in cmd)
        logger.info(f"명령어 실행: {cmd_str}")
        
        if not os.access(script_path, os.X_OK):
            logger.warning(f"스크립트 {script_path}에 실행 권한이 없습니다. 권한을 부여합니다.")
            os.chmod(script_path, 0o755)
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            cwd=PROJECT_ROOT
        )
        
        for line in process.stdout:
            line = line.strip()
            if line:
                logger.info(f"[{step_name}] {line}")
        
        process.wait()
        exit_code = process.returncode
        
        if exit_code != 0:
            logger.error(f"스크립트 실행 실패 (종료 코드: {exit_code})")
            return False, f"스크립트 {os.path.basename(script_path)} 실행 실패 (종료 코드: {exit_code})"
        
        logger.info(f"스크립트 성공적으로 실행됨 (종료 코드: {exit_code})")
        return True, None
    
    except Exception as e:
        error_msg = f"스크립트 실행 중 예외 발생: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg

# --- 중간 결과물 정리 함수 ---
def cleanup_intermediate_results(font_name: str, logger):
    """지정된 폰트 이름에 대한 중간 결과 디렉토리를 정리합니다."""
    logger.info(f"'{font_name}'에 대한 중간 결과물 정리 시작...")
    dirs_to_delete = [
        os.path.join(RESULT_DIR, "1_cropped", font_name),
        os.path.join(RESULT_DIR, "2_inference", font_name),
        os.path.join(RESULT_DIR, "3_svg", font_name)
    ]
    
    for dir_path in dirs_to_delete:
        if os.path.isdir(dir_path):
            try:
                shutil.rmtree(dir_path)
                logger.info(f"  삭제 완료: {dir_path}")
            except Exception as e:
                logger.error(f"  삭제 실패: {dir_path} - {e}")
        else:
            logger.info(f"  삭제 건너뜀 (존재하지 않음): {dir_path}")
    logger.info("중간 결과물 정리 완료.")

# --- API Endpoints ---
@app.post("/font")
async def create_font(request: FontRequest):
    """
    폰트 생성 요청을 수신하고, 스크립트를 순차적으로 실행하며,
    프로세스를 로깅합니다.
    """
    font_name = request.font_name
    
    # 요청에 대한 고유 ID 생성
    request_id = str(uuid.uuid4())
    
    # 로거 설정 및 로그 파일 경로 가져오기
    logger, log_file = setup_logger(request_id, font_name)

    logger.info(f"폰트 생성 요청 수신: {font_name} (요청 ID: {request_id})")

    try:
        logger.info(f"폰트 생성 파이프라인 시작... (요청 ID: {request_id})")
            
        crop_script = os.path.join(SCRIPTS_DIR, "1_crop_glyphs.sh")
        logger.info("글리프 크롭 스크립트 실행 중...")
        success, error = run_script(crop_script, [font_name], logger, "CROP")
        if not success:
            raise Exception(f"글리프 크롭 실패: {error}")
        
        inference_script = os.path.join(SCRIPTS_DIR, "2_run_inference.sh")
        logger.info("추론 스크립트 실행 중...")
        success, error = run_script(inference_script, [font_name], logger, "INFERENCE")
        if not success:
            raise Exception(f"추론 실패: {error}")
        
        jpg2svg_script = os.path.join(SCRIPTS_DIR, "3_run_jpg2svg.sh")
        logger.info("JPG에서 SVG 변환 스크립트 실행 중...")
        success, error = run_script(jpg2svg_script, [font_name], logger, "SVG")
        if not success:
            raise Exception(f"JPG에서 SVG 변환 실패: {error}")
        
        svg2ttf_script = os.path.join(SCRIPTS_DIR, "4_run_svg2ttf.sh")
        logger.info("SVG에서 TTF/WOFF 변환 스크립트 실행 중...")
        success, error = run_script(svg2ttf_script, ["-f", font_name], logger, "TTF/WOFF")
        if not success:
            raise Exception(f"SVG에서 TTF/WOFF 변환 실패: {error}")
        
        logger.info(f"폰트 '{font_name}' 생성 파이프라인이 성공적으로 완료되었습니다. (요청 ID: {request_id})")
        
        result_ttf_path = os.path.join(RESULT_DIR, "4_fonts", f"{font_name}.ttf")
        result_woff_path = os.path.join(RESULT_DIR, "4_fonts", f"{font_name}.woff")
        
        return {
            "message": f"폰트 '{font_name}' 생성 완료",
            "request_id": request_id,
            "log_file": log_file,
            "output_ttf": result_ttf_path,
            "output_woff": result_woff_path,
        }

    except Exception as e:
        error_message = f"폰트 '{font_name}' 생성 중 오류 발생: {str(e)} (요청 ID: {request_id})"
        logger.error(error_message, exc_info=True)
        raise HTTPException(status_code=500, detail=error_message)
    
    finally:
        # 파이프라인 성공/실패 여부와 관계없이 중간 결과 정리
        cleanup_intermediate_results(font_name, logger)

# --- Main Execution (for running with uvicorn) ---
if __name__ == "__main__":
    for subdir in ["1_cropped", "2_inference", "3_svg", "4_fonts"]:
        os.makedirs(os.path.join(RESULT_DIR, subdir), exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(os.path.join(PROJECT_ROOT, "written"), exist_ok=True)
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
import requests
import logging
import json
from fastAPI.config import BACKEND_URL, FONT_PORGRESS_URI, FONT_PORGRESS_URI_METHOD, JWT_TOKEN, FONT_STATUS
    
def send_font_progress_result(font_id, status, log_file, logger = None):
    url = BACKEND_URL + FONT_PORGRESS_URI + f"/{font_id}"
    request_method = FONT_PORGRESS_URI_METHOD
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + JWT_TOKEN,
    }
    payload = {
        "status" : status.name,
        # "log" : log_file,
    }
    
    if not logger:
        logger = logging.getLogger()    
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    logger.info(f"FastAPI 서버 ({url})에 폰트 생성 요청 전송 중...")
    logger.info(f"요청 메서드: {request_method}")
    logger.info(f"요청 헤더: {json.dumps(headers)}")
    logger.info(f"요청 데이터: {json.dumps(payload)}")
    
    # requests 모듈에서 해당 HTTP 메서드를 동적으로 가져오기
    method_function = getattr(requests, request_method.lower(), None)
    if method_function is None:
        logger.error(f"지원하지 않는 HTTP 메서드: {request_method}")
        raise ValueError(f"Unsupported HTTP method: {request_method}")
    
    response = None
    
    try:
        response = method_function(url, headers=headers, json=payload)
        response.raise_for_status()
        
        
        print("\n--- 서버 응답 ---")
        try:
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 텍스트로 출력
            print(response.text)
        print("-----------------")
    
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP 오류 발생: {http_err}")
        raise
    
    except requests.exceptions.ConnectionError:
        print(f"\n오류: 서버({url})에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        raise
    
    finally:    
        if response is not None:
            logger.info(f"응답 상태 코드: {response.status_code}")
            logger.info(f"응답 데이터: {response.text}")
        
    return response
    

## for test
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        font_id = sys.argv[1]
    else:
        font_id = 1
        print("font_id인자가 제공되지 않았습니다. 기본값 '1 사용.")
    send_font_progress_result(font_id, Status.DONE, "log_file_url")
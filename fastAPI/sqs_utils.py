import threading
import logging
import boto3
import json
import time
from fastAPI.config import AWS_REGION, AWS_ACCESS_KEY, AWS_SECRET_KEY, QUEUE_URL, FONT_BUCKET_NAME, FONT_CREATE_LOG_BUCKET_NAME, FONT_STATUS
from fastAPI.s3_utils import download_image_from_s3, upload_file_to_s3
from fastAPI.script_utils import cleanup_intermediate_results
from fastAPI.pipeline_runner import run_font_pipeline
from fastAPI.logger_utils import setup_logger
from fastAPI.prometheus_loki.prometheus_config import SQS_POLL_TOTAL, SQS_PROCESSED_MESSAGES, SQS_PROCESSING_DURATION, SQS_PROCESSING_ERRORS, SQS_RECEIVED_MESSAGES
from fastAPI.font_create_result_requests import send_font_progress_result

sqs = boto3.client(
    "sqs", 
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)

no_message_logged = False

# 메시지 키 상수를 정의합니다.
MEMBER_ID_KEY = "memberId"
AUTHOR_KEY = "author"
FONT_FILE_KEY = "fileKey"
FONT_ID_KEY = "fontId"
FONT_NAME_KEY = "fontName"
FONT_ENG_NAME_KEY= "fontEngName"
TEMPLATE_URL_KEY = "templateURL"
REQUEST_UUID_KEY = "requestUUID"

# SQS 메시지 형식
# {
#   "fontId": "231",
#   "memberId": "213123",
#   "fileKey": "uuid..."
#   "fontName": "testFontName",
#   "templateURL": "https://....",
#   "author": "author",
#   "requestUUID": "sadsadsa"
# }

sqs_message_properties = [FONT_ID_KEY, FONT_FILE_KEY, MEMBER_ID_KEY, FONT_NAME_KEY, FONT_ENG_NAME_KEY, TEMPLATE_URL_KEY, AUTHOR_KEY, REQUEST_UUID_KEY]

def validation_SQS_message(msg):
    try:
        body_raw = msg[0].get('Body', '')
        body = json.loads(body_raw)

        if not isinstance(body, dict):
            logging.error(f"[SQS] 지원하지 않는 메시지 형식입니다.")
            raise ValueError("지원하지 않는 메시지 형식입니다.")
        for property in sqs_message_properties:
            if property not in body or not body.get(property):
                logging.error(f"[SQS] '{property}' 필드가 없습니다.")
                raise ValueError(f"'{property}' 필드가 없습니다.")
        return body

    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logging.error(f"[SQS] 메시지 파싱 실패: {e}")
        logging.error(f"[SQS] 원본 메시지: {msg}")
        raise

def poll_sqs():
    global no_message_logged
    while True:
        SQS_POLL_TOTAL.inc() # SQS 폴링 시도 횟수 증가
        
        try:
            response = sqs.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20
            )
            
            messages = response.get("Messages", [])
            if not messages:
                if not no_message_logged:
                    logging.info("No message received, waiting...")
                    no_message_logged = True
                continue
            
            SQS_RECEIVED_MESSAGES.inc()
            no_message_logged = False
            msg = messages[0]
            logging.info(f"[SQS] Received raw message: {msg}")
            
            body = validation_SQS_message(messages)
            logging.info(f"[SQS] Parsed message body: {body}")
            
            # SQS 메시지 처리 시간을 측정
            with SQS_PROCESSING_DURATION.time():
                font_id = str(body.get(FONT_ID_KEY))
                font_file_key = str(body.get(FONT_FILE_KEY))
                font_name = body.get(FONT_NAME_KEY)
                font_eng_name = body.get(FONT_ENG_NAME_KEY)
                template_url = body.get(TEMPLATE_URL_KEY)
                request_member_id = str(body.get(MEMBER_ID_KEY))
                requestUUID = body.get(REQUEST_UUID_KEY)
                
                ttf_s3_url = ""
                woff_s3_url = ""
                log_s3_url = ""
                
                # for metadata
                author = body.get(AUTHOR_KEY)
                
                logger, log_file = setup_logger(requestUUID, request_member_id, font_id, font_name)
                logger.info(f"폰트 생성 요청 수신: {font_name}")
            
                # 전체 처리 로직 시작
                try:
                    # 템플릿 다운로드
                    _, image_path = download_image_from_s3(request_member_id, font_name, template_url, logger)
                    logger.info(f"템플릿 다운로드 완료: {image_path}")
                
                    # 폰트 제작 로직
                    result_ttf_path, result_woff_path = run_font_pipeline(font_name, font_eng_name, requestUUID, logger)
                    logger.info(f"폰트 '{font_name}' 생성 성공")
                    
                    # 폰트 파일 S3업로드 
                    _, ttf_s3_url = upload_file_to_s3(result_ttf_path, "fonts/" + font_file_key + ".ttf", FONT_BUCKET_NAME, logger)
                    logger.info(f"폰트 파일 업로드 완료: {ttf_s3_url}")
                    
                    _, woff_s3_url = upload_file_to_s3(result_woff_path, "fonts/" + font_file_key + ".woff2", FONT_BUCKET_NAME, logger)
                    logger.info(f"웹폰트 파일 업로드 완료: {woff_s3_url}")
                    
                    ## 백엔드 서버에 폰트 생성 결과 PATCH 요청
                    try:
                        logger.info(f"백엔드 서버 폰트 생성 결과 PATCH 요청")
                        send_font_progress_result(font_id, FONT_STATUS.DONE, log_s3_url, logger)
                        logger.info(f"백엔드 서버 폰트 생성 결과 PATCH 요청 성공")
                    except Exception as e:
                        logger.info(f"백엔드 서버 폰트 생성 결과 PATCH 요청 실패: {e}")
                        raise
                    
                    #정상 요청인 경우에만 SQS 메시지 삭제
                    logger.info(f"[SQS] 메시지 삭제 요청")
                    sqs.delete_message(
                        QueueUrl=QUEUE_URL,
                        ReceiptHandle=msg["ReceiptHandle"]
                    )
                    logger.info(f"[SQS] 메시지 삭제 완료")
                    SQS_PROCESSED_MESSAGES.inc() # 정상 처리된 메시지 건수 증가
                    logger.info(f"폰트 생성 처리 완료")
                    
                # 성공 여부 상관없이 로그 파일 업로드, cleanup 실행    
                finally:
                    try:
                        _, log_s3_url = upload_file_to_s3(log_file, font_id + ".log", FONT_CREATE_LOG_BUCKET_NAME, logger)
                        logger.info(f"로그 파일 업로드 완료: {log_s3_url}")
                    except Exception as log_err:
                        logger.error(f"로그 파일 업로드 실패: {log_err}")
                    cleanup_intermediate_results(font_name, logger)

        except Exception as e:
            SQS_PROCESSING_ERRORS.inc() # 에러 발생 건수 증가
            logging.error(f"[SQS] Error occured during process messages: {e}")
        time.sleep(1)

def start_sqs_polling():
    thread = threading.Thread(target=poll_sqs, daemon=True)
    thread.start()
    logging.info("SQS polling thread started")
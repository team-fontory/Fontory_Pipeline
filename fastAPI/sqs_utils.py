import json
import logging
import time
import threading
import boto3
import uuid
from fastAPI.config import AWS_REGION, AWS_ACCESS_KEY, AWS_SECRET_KEY, QUEUE_URL
from fastAPI.script_utils import cleanup_intermediate_results
from fastAPI.pipeline_runner import run_font_pipeline
from fastAPI.logger_utils import setup_logger
from fastAPI.s3_utils import download_image_from_s3

sqs = boto3.client(
    "sqs", 
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)

no_message_logged = False

# 메시지 키 상수를 정의합니다.
FONT_NAME_KEY = "fontName"
TEMPLATE_URL_KEY = "templateURL"
MEMBER_ID_KEY = "memberId"
REQUEST_UUID = "requestUUID"

properties = [FONT_NAME_KEY, TEMPLATE_URL_KEY, MEMBER_ID_KEY, REQUEST_UUID]

def validation_SQS_message(msg):
    try:
        body_raw = msg[0].get('Body', '')
        body = json.loads(body_raw)

        if not isinstance(body, dict):
            logging.error(f"[SQS] 지원하지 않는 메시지 형식입니다.")
            raise ValueError("지원하지 않는 메시지 형식입니다.")
        for property in properties:
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
        try:
            response = sqs.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10
            )
            messages = response.get("Messages", [])
            if not messages:
                if not no_message_logged:
                    logging.info("No message received, waiting...")
                    no_message_logged = True
                continue
            
            no_message_logged = False
            msg = messages[0]
            logging.info(f"[SQS] Received raw message: {msg}")
            
            body = validation_SQS_message(messages)
            logging.info(f"[SQS] Parsed message body: {body}")
            
            font_name = body.get(FONT_NAME_KEY)
            template_url = body.get(TEMPLATE_URL_KEY)
            request_member_id = body.get(MEMBER_ID_KEY)
            requestUUID = body.get(REQUEST_UUID)
            
            # requestUUID = str(uuid.uuid4())
            logger, log_file = setup_logger(requestUUID, request_member_id, font_name)
            logger.info(f"폰트 생성 요청 수신: {font_name})")
        
            _, image_path = download_image_from_s3(request_member_id, font_name, template_url, logger)
            logger.info(f"템플릿 다운로드 완료: {image_path}")
            
            # 폰트 제작 로직
            try:
                result_ttf_path, result_woff_path = run_font_pipeline(font_name, requestUUID, logger)
                logger.info(f"폰트 '{font_name}' 생성 성공")
            finally:
                cleanup_intermediate_results(font_name, logger)
        
            #정상 요청인 경우에만 메시지 삭제
            logger.info(f"[SQS] 메시지 삭제 요청")
            sqs.delete_message(
                QueueUrl=QUEUE_URL,
                ReceiptHandle=msg["ReceiptHandle"]
            )
            logger.info(f"[SQS] 메시지 삭제 완료")
                
        except Exception as e:
            logging.error(f"[SQS] Error occured during process messages: {e}")
        time.sleep(1)

def start_sqs_polling():
    thread = threading.Thread(target=poll_sqs, daemon=True)
    thread.start()
    logging.info("SQS polling thread started")
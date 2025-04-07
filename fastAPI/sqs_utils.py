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

sqs = boto3.client(
    "sqs", 
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)

no_message_logged = False

def validation_SQS_message(msg):
    try:
        body_raw = msg[0].get('Body', '')
        body = json.loads(body_raw)

        # 조건 추가해야함 
        if not isinstance(body, dict) or "fontName" not in body:
            raise ValueError("지원하지 않는 메시지 형식입니다. 'fontName' 필드가 없습니다.")

        return body

    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logging.error(f"[SQS] 메시지 파싱 실패: {e}")
        logging.error(f"[SQS] 원본 메시지: {msg}")
        raise ValueError("SQS 메시지 형식이 잘못되었습니다.") from e

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
            
            try:
                body = validation_SQS_message(messages)
                logging.info(f"[SQS] Parsed message body: {body}")
            
                font_name = body.get("fontName")
                if not font_name:
                    logging.error(f"폰트 이름이 존재하지 않습니다.")
                    continue
            
                request_id = str(uuid.uuid4())
                logger, log_file = setup_logger(request_id, font_name)
                logger.info(f"폰트 생성 요청 수신: {font_name})")
            
                try:
                    # 나중에 S3 업로드에 사용
                    result_ttf_path, result_woff_path = run_font_pipeline(font_name, request_id, logger)
                    logger.info(f"폰트 '{font_name}' 생성 성공")
                except Exception as ee:
                    logger.error(f"폰트 생성 중 오류 발생: {str(e)}")
                finally:
                    cleanup_intermediate_results(font_name, logger)
            
                #정상 요청인 경우에만 메시지 삭제
                logger.info(f"sqs 메시지 삭제 요청")
                sqs.delete_message(
                    QueueUrl=QUEUE_URL,
                    ReceiptHandle=msg["ReceiptHandle"]
                )
                logger.info(f"sqs 메시지 삭제 완료")
                
            except Exception as e:
                logging.error(f"[SQS] 메시지 처리 중 오류 발생: {e}")
                            
        except Exception as e:
            logging.error(f"[SQS] Polling error: {e}")
        time.sleep(1)

def start_sqs_polling():
    thread = threading.Thread(target=poll_sqs, daemon=True)
    thread.start()
    logging.info("SQS polling thread started")
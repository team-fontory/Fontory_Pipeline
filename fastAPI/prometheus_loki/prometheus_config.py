from prometheus_client import Counter, Histogram

# SQS 폴링 시도 횟수를 기록
SQS_POLL_TOTAL = Counter(
    'sqs_poll_total', 
    'Total number of SQS poll attempts'
)

# 성공적으로 처리한 메시지 수 (삭제되기 전의 정상 처리 건수)
SQS_PROCESSED_MESSAGES = Counter(
    'sqs_processed_messages_total', 
    'Total number of SQS messages processed successfully'
)

# 처리 중 에러가 발생한 메시지 수
SQS_PROCESSING_ERRORS = Counter(
    'sqs_processing_errors_total', 
    'Total number of SQS message processing errors'
)

# 하나의 SQS 메시지를 처리하는 데 걸린 시간 (초 단위)
SQS_PROCESSING_DURATION = Histogram(
    'sqs_processing_duration_seconds', 
    'Time spent processing an SQS message',
    buckets=(30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 360, 420, 480) 
)
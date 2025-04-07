# 폰트 파이프라인 API 서버

사용자 손글씨를 기반으로 폰트를 자동 생성하는 파이프라인 API 서버입니다.

## 기능

- FastAPI 기반 REST API 서버
- 파이프라인 단계별 자동 실행
- 상세 로깅
- 오류 식별 및 처리

## 파이프라인 단계

1. **글리프 크롭** - 작성된 문자 이미지를 개별 글리프로 추출
2. **추론 실행** - 딥러닝 모델을 사용한 글리프 생성
3. **JPG → SVG 변환** - 비트맵 이미지를 벡터 형식으로 변환
4. **SVG → TTF/WOFF 변환** - 벡터 글리프를 폰트 파일로 변환

## 요구사항 및 구조

### 요구 사항

- Python 3.8 이상
- Docker
- pip

### 디렉토리 구조

```
pipeline/
├── fastAPI/            # FastAPI 애플리케이션 코드
├── jpg2svg/            # JPG to SVG 변환 관련 코드
├── svg2ttf/            # SVG to TTF 변환 관련 코드
├── make_template/      # 템플릿 생성 관련 코드
├── inference/          # 모델 추론 관련 코드
├── crop/               # 이미지 크롭 관련 코드
├── scripts/            # 파이프라인 단계별 실행 스크립트
├── resource/           # 프로젝트 리소스 파일
├── run_server.sh       # 서버 실행 스크립트
├── stop_server.sh      # 서버 중지 스크립트
├── test_request.py     # 서버 테스트 스크립트
├── reference_chars.txt # 폰트 생성용 참조 문자 파일
├── written/            # 사용자 작성 이미지 입력
├── result/             # 파이프라인 결과 디렉토리
│   ├── 1_cropped/      # 크롭된 글리프
│   ├── 2_inference/    # 추론 결과
│   ├── 3_svg/          # SVG 변환 결과
│   └── 4_fonts/        # 최종 폰트 파일
└── log/                # 실행 로그 파일
```

### 환경 변수 설정

이 프로젝트는 AWS 서비스와의 연동을 위해 환경 변수를 사용합니다. 프로젝트 루트의 `fastAPI` 디렉토리 내에 `.env` 파일을 생성하고 다음 변수들을 설정해야 합니다:

```dotenv
AWS_REGION=your_aws_region
AWS_ACCESS_KEY=your_aws_access_key
AWS_SECRET_KEY=your_aws_secret_key
QUEUE_URL=your_sqs_queue_url
```

- `AWS_REGION`: 사용하는 AWS 리전 (예: `ap-northeast-2`)
- `AWS_ACCESS_KEY`: AWS IAM 사용자의 액세스 키 ID
- `AWS_SECRET_KEY`: AWS IAM 사용자의 비밀 액세스 키
- `QUEUE_URL`: 폰트 생성 요청을 처리할 SQS 큐의 URL

## 사용 방법

### 권한 부여
```
chmod +x ./scripts/*
chmod +X ./*.sh
```

### 0. 템플릿 생성
```bash
./scripts/0_generate_template.sh
```


### 1. 이미지 준비
위에서 생성된 템플릿을 다운받고 손글씨로 작성된 이미지 파일(.jpg) 을 `./written` 디렉토리에 저장합니다. 


### 2. API 서버 실행

```bash
./run_server.sh
```
서버 실행 시 다음 작업이 수행됩니다:
- 필요한 디렉토리 구조 생성
- Python 가상 환경 설정
- 의존성 패키지 설치
- FastAPI 서버 실행


### 3-1. API 서버 호출

```bash
# 테스트 스크립트 사용
python test_request.py MyCustomFont

# 또는 curl 사용
curl -X POST "http://localhost:8000/font" \
     -H "Content-Type: application/json" \
     -d '{"font_name": "MyNewFont"}'
```

### 3-2. SQS 큐 직접 호출

API 서버를 통하지 않고 직접 AWS SQS 큐에 메시지를 보내 파이프라인 실행을 트리거할 수도 있습니다. 이는 대량 처리나 다른 시스템과의 연동 시 유용할 수 있습니다.

AWS CLI를 사용하여 메시지를 보낼 수 있습니다. `.env` 파일에 설정된 `QUEUE_URL`을 사용해야 합니다.

(참고: AWS CLI를 사용하려면 AWS 자격 증명 설정이 필요합니다. `aws configure` 명령어나 환경 변수 등을 통해 설정할 수 있습니다.)

```bash
aws sqs send-message --queue-url YOUR_SQS_QUEUE_URL --message-body '{"font_name": "MySQSFont"}' --message-group-id MyFontGroup
```

- `YOUR_SQS_QUEUE_URL`: `.env` 파일에 설정한 SQS 큐 URL로 변경해야 합니다.
- `--message-body`: 폰트 이름을 포함하는 JSON 형식의 메시지 본문입니다.
- `--message-group-id`: FIFO 큐의 경우 메시지 그룹 ID가 필요합니다. 동일한 그룹 ID 내에서는 메시지 순서가 보장됩니다. 폰트 이름이나 사용자 ID 등 적절한 값을 사용합니다.

### 4. 서버 중지

```bash
./stop_server.sh
```

## API 명세

### POST /font

폰트 생성 작업을 요청합니다.

**요청 본문:**
```json
{
  "font_name": "MyNewFont"
}
```

**응답:**
```json
{
  "message": "폰트 'MyNewFont' 생성 완료",
  "request_id": "1b34a6cd-5e78-12d3-a456-426614174000",
  "log_file": "./log/20230401_123456_1b34a6_MyNewFont.log",
  "output_ttf": "./result/4_fonts/MyNewFont.ttf",
  "output_woff": "./result/4_fonts/MyNewFont.woff"
}
```

## API 문서

Swagger UI 문서 접근 URL:
```
http://localhost:8000/docs
```

## 로그

각 요청은 고유 ID와 타임스탬프가 포함된 로그 파일에 기록됩니다:
```
./log/[시간]_[UUID]_[폰트이름].log
``` 
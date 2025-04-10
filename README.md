# 폰트 파이프라인 API 서버

사용자 손글씨를 기반으로 폰트를 자동 생성하는 파이프라인 서버입니다.

## 기능

- FastAPI 기반 API 테스트 서버
- AWS SQS 기반 자동화 파이프라인
- 한국어 손글씨 폰트 자동 생성
- 상세 로깅 및 오류 처리
- AWS S3 파일 자동 처리 (업로드/다운로드)

## 동작 방식

이 프로젝트는 두 가지 방식으로 동작합니다:

1. **FastAPI 서버 (테스트 용도)**: 
   - 폰트 생성 기능만 제공
   - 로컬 테스트 및 개발 환경에서 사용 

2. **AWS SQS 기반 파이프라인**:
   - SQS 큐를 지속적으로 폴링하며 메시지 수신 대기
   - 메시지 수신 시 자동으로 폰트 생성 파이프라인 시작
   - S3에서 템플릿 다운로드
   - 폰트 생성
   - 생성된 폰트 및 로그 파일 S3 업로드
   - 처리 완료 후 SQS 메시지 자동 삭제

## 파이프라인 단계

0. **S3 템플릿 다운로드** - AWS S3에 저장된 템플릿을 다운로드 (SQS 모드에서만 실행)
1. **글리프 크롭** - 작성된 문자 이미지를 개별 글리프로 추출 (Docker 컨테이너로 실행)
2. **추론 실행** - 딥러닝 모델을 사용한 글리프 생성 (Docker 컨테이너로 실행)
3. **JPG → SVG 변환** - 비트맵 이미지를 벡터 형식으로 변환 (Docker 컨테이너로 실행)
4. **SVG → TTF/WOFF 변환** - 벡터 글리프를 폰트 파일로 변환 (Docker 컨테이너로 실행)
5. **S3 업로드** - 생성된 폰트 및 결과물을 AWS S3에 업로드 (SQS 모드에서만 실행)

**참고:** S3 연계(템플릿 다운로드 및 결과물 업로드)를 제외한 모든 파이프라인 단계는 Docker 컨테이너로 실행됩니다. 각 단계는 독립적인 Docker 컨테이너에서 실행되며, 중간 결과물은 호스트 시스템의 공유 볼륨을 통해 전달됩니다.

## 모델 파일 설정

이 프로젝트는 한국어 글꼴 생성을 위해 DM-FONT 모델을 사용합니다. 모델 파일(체크포인트)은 다음 위치에 배치해야 합니다:

```
inference/resources/checkpoints/
                               └── last.pth  # 모델 체크포인트 파일
```

모델 파일을 배치한 후에 파이프라인이 올바르게 동작합니다.

## 요구사항 및 구조

### 요구 사항

- Python 3.8 이상
- Docker
- pip
- Ubuntu 20.04 LTS 이상 (권장)
- NVIDIA GPU: 최소 8GB VRAM (권장 12GB 이상, 추론 모델 실행용)

### 디렉토리 구조

```
pipeline/                    # 프로젝트 루트 디렉토리
│
├── crop/                    # 이미지 크롭 관련 코드
├── jpg2svg/                 # JPG to SVG 변환 관련 코드
├── make_template/           # 템플릿 생성 관련 코드
├── svg2ttf/                 # SVG to TTF 변환 관련 코드
├── inference/               # 모델 추론 관련 코드
│   └── resources/checkpoints/
│       └── last.pth         # 모델 체크포인트 파일
│
├── scripts/                 # 파이프라인 단계별 실행 스크립트
│
├── fastAPI/                 # FastAPI 애플리케이션 코드
│   ├── config.py            # 설정 관리
│   ├── main.py              # 서버 진입점
│   ├── models.py            # 데이터 모델 정의
│   ├── s3_utils.py          # S3 관련 유틸리티
│   ├── sqs_utils.py         # SQS 관련 유틸리티
│   ├── prometheus_loki/     # Prometheus 및 Loki 모니터링 설정
│   │   ├── compose.yml      # 모니터링 서비스 Docker Compose 파일
│   │   ├── prometheus.config # Prometheus 설정 파일
│   │   ├── prometheus_api.py # Prometheus API 통합 코드
│   │   └── prometheus_config.py # Prometheus 설정 관리
│   └── .env                 # 환경 변수 설정 파일
│
├── resource/                # 프로젝트 리소스 파일
├── written/                 # 사용자 작성 이미지 입력
├── log/                     # 실행 로그 파일
│
├── result/                  # 파이프라인 결과 디렉토리
│   ├── 1_cropped/           # 크롭된 글리프
│   ├── 2_inference/         # 추론 결과
│   ├── 3_svg/               # SVG 변환 결과
│   └── 4_fonts/             # 최종 폰트 파일
│
├── reference_chars.txt      # 폰트 생성용 참조 문자 파일
├── run_server.sh            # 서버 실행 스크립트
├── stop_server.sh           # 서버 중지 스크립트
└── test_request.py          # 서버 테스트 스크립트
```

## 환경 변수 설정

이 프로젝트는 AWS 서비스와의 연동을 위해 환경 변수를 사용합니다. 프로젝트 루트의 `fastAPI` 디렉토리 내에 `.env` 파일을 생성하고 다음 변수들을 설정해야 합니다:

```dotenv
AWS_REGION=your_aws_region
AWS_ACCESS_KEY=your_aws_access_key
AWS_SECRET_KEY=your_aws_secret_key
QUEUE_URL=your_sqs_queue_url
FONT_BUCKET_NAME=your_font_bucket_name
FONT_CREATE_LOG_BUCKET_NAME=your_log_bucket_name
```

- `AWS_REGION`: 사용하는 AWS 리전 (예: `ap-northeast-2`)
- `AWS_ACCESS_KEY`: AWS IAM 사용자의 액세스 키 ID
- `AWS_SECRET_KEY`: AWS IAM 사용자의 비밀 액세스 키
- `QUEUE_URL`: 폰트 생성 요청을 처리할 SQS 큐의 URL
- `FONT_BUCKET_NAME`: 생성된 폰트 파일을 업로드할 S3 버킷 이름
- `FONT_CREATE_LOG_BUCKET_NAME`: 로그 파일을 업로드할 S3 버킷 이름

### AWS 권한 요구사항

AWS IAM 사용자는 다음 권한이 필요합니다:

1. **SQS 관련 권한**:
   - `sqs:ReceiveMessage` - 큐에서 메시지를 받아오는 권한
   - `sqs:DeleteMessage` - 처리 완료된 메시지를 삭제하는 권한

2. **S3 관련 권한**:
   - `s3:PutObject` - 생성된 폰트 파일(.ttf, .woff)과 로그 파일을 업로드하는 권한
   - 버킷 정책에 따라 다음 경로에 대한 업로드 권한 필요:
     - `[FONT_BUCKET_NAME]/fonts/*` - 폰트 파일 저장 경로
     - `[FONT_CREATE_LOG_BUCKET_NAME]/logs/*` - 로그 파일 저장 경로

3. **템플릿 이미지 접근성**:
   - 템플릿 이미지가 저장된 S3 버킷/객체는 공개적으로 접근 가능해야 합니다.
   - 또는 SQS 메시지의 `templateURL` 필드에 유효한 미리 서명된 URL(pre-signed URL)을 제공해야 합니다.
   - 코드는 `urllib.request.urlretrieve`를 사용하여 HTTP URL을 통해 직접 다운로드하므로 S3 인증이 필요하지 않습니다.

이러한 권한이 있는 IAM 사용자의 ACCESS_KEY와 SECRET_KEY를 입력해야 합니다.

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


### 1. 이미지 준비 (테스트용 API 전용)
**참고: 이 단계는 테스트용 API를 사용할 때만 필요합니다. SQS 방식에서는 S3에서 템플릿을 자동으로 다운로드하므로 이 단계를 건너뛸 수 있습니다.**

위에서 생성된 템플릿을 다운받고 손글씨로 작성된 이미지 파일(.jpg) 을 `./written` 디렉토리에 저장합니다. 


### 2. 서버 실행


```bash
./run_server.sh
```
서버 실행 시 다음 작업이 수행됩니다:
- 필요한 디렉토리 구조 생성
- Python 가상 환경 설정
- 의존성 패키지 설치
- Prometheus 및 Loki 모니터링 서비스 시작 (Docker Compose 사용)
- FastAPI 서버 실행

### 3. 폰트 생성 요청

#### 3-1. API 서버 호출 (테스트용)

로컬 API 서버를 통해 폰트 생성을 테스트할 수 있습니다. 이 방식은 **폰트 생성**만 수행하며 S3 업로드는 포함하지 않습니다.

```bash
# 테스트 스크립트 사용
python test_request.py MyCustomFont

# 또는 curl 사용
curl -X POST "http://localhost:8000/font" \
     -H "Content-Type: application/json" \
     -d '{
       "fontId": "231", 
       "memberId": "213123", 
       "fontName": "testFontName", 
       "templateURL": "https://....", 
       "author": "author", 
       "requestUUID": "550e8400-e29b-41d4-a716-446655440000"
     }'
```

#### 3-2. SQS 큐 직접 호출

AWS SQS 큐에서 메시지를 받아와 파이프라인을 실행합니다. 이 방식은 **템플릿 다운로드 + 폰트 생성 + 폰트 및 로그 S3 업로드**를 모두 수행합니다.

AWS CLI 혹은 AWS 콘솔을 통해 직접 SQS에 메시지를 보낼 수 있습니다. `.env` 파일에 설정된 `QUEUE_URL`을 사용해야 합니다.

(참고: AWS CLI를 사용하려면 AWS 자격 증명 설정이 필요합니다. `aws configure` 명령어나 환경 변수 등을 통해 설정할 수 있습니다.)

```bash
aws sqs send-message --queue-url YOUR_SQS_QUEUE_URL \
     --message-body '{
       "memberId": "213123",
       "author": "author",
       "fontId": "231",
       "fontName": "testFontName",
       "templateURL": "https://....",
       "requestUUID": "550e8400-e29b-41d4-a716-446655440000"
     }' \
     --message-group-id MyFontGroup
```

- `YOUR_SQS_QUEUE_URL`: `.env` 파일에 설정한 SQS 큐 URL로 변경해야 합니다.
- `--message-body`: 폰트 관련 정보를 포함하는 JSON 형식의 메시지 본문입니다.
- `--message-group-id`: FIFO 큐의 경우 메시지 그룹 ID가 필요합니다. 동일한 그룹 ID 내에서는 메시지 순서가 보장됩니다. 폰트 이름이나 사용자 ID 등 적절한 값을 사용합니다.

### 4. 서버 중지 

다음 서버를 명령으로 중지할 수 있습니다:

```bash
./stop_server.sh
```

이 명령어는 다음 작업을 수행합니다:
- Prometheus 및 Loki 모니터링 서비스 중지 (Docker Compose 사용)
- 포트 8000에서 실행 중인 FastAPI 서버 프로세스 종료

## 모니터링 시스템

이 프로젝트는 애플리케이션 모니터링을 위해 Prometheus와 Loki를 통합했습니다:

### Prometheus

- 메트릭 수집 및 모니터링을 위한 오픈소스 시스템
- 포트 9090에서 접근 가능 (http://localhost:9090/prometheus)
- API 요청 수, 응답 시간, 오류율 등의 메트릭 수집

### Loki

- 로그 집계 시스템
- 포트 3100에서 접근 가능
- 애플리케이션 로그를 중앙 집중식으로 저장 및 조회 가능

모니터링 서비스는 Docker Compose를 통해 관리되며, `run_server.sh` 및 `stop_server.sh` 스크립트에 통합되어 있습니다.

**참고:** Prometheus와 Loki는 Grafana의 데이터 소스로 추가하여 사용할 수 있습니다. Grafana에서 Prometheus(9090 포트)와 Loki(3100 포트)를 데이터 소스로 등록하면 메트릭과 로그 데이터를 시각화하고 모니터링 대시보드를 구성할 수 있습니다.

## API 명세

### POST /font (테스트용)

테스트용 로컬 API 엔드포인트로, 폰트 생성만 수행합니다. S3 업로드는 포함하지 않습니다.

**요청 본문:**
```json
{
  "fontId": "231",
  "memberId": "213123",
  "fontName": "testFontName",
  "templateURL": "https://....",
  "author": "author",
  "requestUUID": "550e8400-e29b-41d4-a716-446655440000"
}
```

**응답:**
```json
{
  "message": "폰트 'testFontName' 생성 완료",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "log_file": "./log/550e84_213123_231_testFontName.log",
  "output_ttf": "./result/4_fonts/testFontName.ttf",
  "output_woff": "./result/4_fonts/testFontName.woff"
}
```

## SQS 메시지 형식

SQS 큐에 메시지를 전송하면 완전한 파이프라인(템플릿 다운로드, 폰트 생성, S3 업로드)이 실행됩니다.

**메시지 형식:**
```json
{
  "memberId": "213123",
  "author": "author",
  "fontId": "231",
  "fontName": "testFontName",
  "templateURL": "https://....",
  "requestUUID": "550e8400-e29b-41d4-a716-446655440000"
}
```

**처리 결과:**
- 템플릿 다운로드 (templateURL에서)
- 폰트 파일 생성 (.ttf, .woff)
- 생성된 폰트 및 로그 파일 S3 업로드
- 완료 시 S3에 다음 파일들이 업로드됩니다:
  - `[FONT_BUCKET_NAME]/fonts/[fontId].ttf`
  - `[FONT_BUCKET_NAME]/fonts/[fontId].woff`
  - `[FONT_CREATE_LOG_BUCKET_NAME]/logs/[fontId].log`

**참고:** 처리 과정에서 오류가 발생하더라도 로그 파일은 S3에 업로드됩니다.

## API 문서

Swagger UI 문서 접근 URL (로컬 API 서버 실행 시):
```
http://localhost:8000/docs
```

## 로그

각 요청은 고유 ID와 사용자 정보가 포함된 로그 파일에 기록됩니다:

### API 모드 및 SQS 모드 로컬 로그 형식
```
./log/[short-requestUUID]_[memberId]_[fontId]_[fontName].log
```

예시: `./log/550e84_213123_231_testFontName.log`

### SQS 모드 S3 업로드 형식
SQS 모드에서는 로그 파일이 로컬에 저장된 후 S3에도 업로드됩니다. S3에 업로드될 때는 다음 형식을 사용합니다:

```
[FONT_CREATE_LOG_BUCKET_NAME]/[fontId].log
```
   
예시: `font_log_bucket/231.log`

SQS 처리가 완료되면 로컬 로그 파일과 S3에 업로드된 로그 파일 모두 사용 가능합니다.
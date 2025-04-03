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
├── main.py             # FastAPI 서버 코드
├── requirements.txt    # 의존성 패키지
├── run_server.sh       # 서버 실행 스크립트
├── stop_server.sh      # 서버 중지 스크립트
├── test_request.py     # API 테스트 스크립트
├── scripts/            # 파이프라인 스크립트
│   ├── 0_generate_template.sh
│   ├── 1_crop_glyphs.sh
│   ├── 2_run_inference.sh
│   ├── 3_run_jpg2svg.sh
│   └── 4_run_svg2ttf.sh
├── result/             # 결과 디렉토리
│   ├── 1_cropped/      # 크롭된 글리프
│   ├── 2_inference/    # 추론 결과
│   ├── 3_svg/          # SVG 변환 결과
│   └── 4_fonts/        # 최종 폰트 파일
├── written/            # 사용자 작성 이미지 입력
└── log/                # 로그 파일
```


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


### 3. API 호출

```bash
# 테스트 스크립트 사용
python test_request.py MyCustomFont

# 또는 curl 사용
curl -X POST "http://localhost:8000/font" \
     -H "Content-Type: application/json" \
     -d '{"font_name": "MyNewFont"}'
```


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
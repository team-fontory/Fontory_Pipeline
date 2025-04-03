#!/bin/bash

# 글리프 크로퍼 Docker 컨테이너를 빌드하고 실행하는 스크립트

# 인자 처리
if [ -z "$1" ]; then
    FONT_NAME="default_font_name"
    echo "폰트 이름이 주어지지 않았습니다. 기본값 'default_font_name'을 사용합니다."
else
    FONT_NAME="$1"
    echo "폰트 이름: '$FONT_NAME'을(를) 사용합니다."
fi

# 경로 설정
CROPPER_IMAGE_NAME="fontory-cropper"
PROJECT_ROOT=$(dirname "$0")/..
HOST_OUTPUT_DIR="$PROJECT_ROOT/result/1_cropped/$FONT_NAME"
HOST_WRITTEN_DIR="$PROJECT_ROOT/written"
HOST_DEBUG_DIR="$HOST_OUTPUT_DIR/debug"

# 출력 및 디버그 디렉토리 생성
mkdir -p "$HOST_OUTPUT_DIR"
mkdir -p "$HOST_DEBUG_DIR"

# Docker 이미지 빌드 (필요시)
if ! docker image inspect $CROPPER_IMAGE_NAME > /dev/null 2>&1; then
    echo "크로퍼 Docker 이미지를 찾을 수 없습니다. 빌드를 시작합니다..."
    docker build -t $CROPPER_IMAGE_NAME -f "$PROJECT_ROOT/crop/cropper.Dockerfile" "$PROJECT_ROOT"
    if [ $? -ne 0 ]; then
        echo "Docker 빌드 실패. 종료합니다."
        exit 1
    fi
else
    echo "크로퍼 Docker 이미지를 찾았습니다. 빌드를 건너니다."
fi

echo "크로퍼 컨테이너를 실행합니다..."

# 컨테이너 실행
docker run --rm \
    -v "$(realpath "$HOST_WRITTEN_DIR")":/app/written \
    -v "$(realpath "$HOST_OUTPUT_DIR")":/app/cropped \
    -v "$(realpath "$HOST_DEBUG_DIR")":/app/debug_output \
    $CROPPER_IMAGE_NAME /app/glyph_cropper.py /app/written /app/cropped

# 실행 결과 확인
if [ $? -ne 0 ]; then
    echo "컨테이너 실행 중 크롭 작업 실패."
    exit 1
else
    echo "크롭 작업 완료."
    echo "  - 글리프: $HOST_OUTPUT_DIR"
    echo "  - 디버그 이미지: $HOST_DEBUG_DIR"
fi
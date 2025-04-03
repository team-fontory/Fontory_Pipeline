#!/bin/bash

# 글리프 크로퍼 Docker 컨테이너를 빌드하고 실행하는 스크립트

# Argument parsing for font name
if [ -z "$1" ]; then
    FONT_NAME="default_font_name"
    echo "폰트 이름이 주어지지 않았습니다. 기본값 'default_font_name'을 사용합니다."
else
    FONT_NAME="$1"
    echo "폰트 이름: '$FONT_NAME'을(를) 사용합니다."
fi

CROPPER_IMAGE_NAME="fontory-cropper" # 크로퍼 Docker 이미지 이름
# 스크립트가 ./scripts에 있으므로, PROJECT_ROOT는 상위 디렉토리
PROJECT_ROOT=$(dirname "$0")/.. # 프로젝트 루트 디렉토리
# Output directory based on font name
HOST_OUTPUT_DIR="$PROJECT_ROOT/result/1_cropped/$FONT_NAME" # 호스트 출력 디렉토리 (업데이트된 경로)
HOST_WRITTEN_DIR="$PROJECT_ROOT/written" # 입력 디렉토리 (템플릿 이미지)
# Debug directory within the font-specific output directory
HOST_DEBUG_DIR="$HOST_OUTPUT_DIR/debug" # 호스트 디버그 출력 디렉토리

# 호스트에 출력 및 디버그 디렉토리가 존재하는지 확인하고 없으면 생성
mkdir -p "$HOST_OUTPUT_DIR"
mkdir -p "$HOST_DEBUG_DIR"
# mkdir -p "$PROJECT_ROOT/debug_crops" # 더 이상 필요 없음, 디버그는 cropped/ 하위 디렉토리에 저장됨

# 크로퍼 Docker 이미지가 이미 존재하는지 확인
if ! docker image inspect $CROPPER_IMAGE_NAME > /dev/null 2>&1; then
    echo "크로퍼 Docker 이미지를 찾을 수 없습니다. 빌드를 시작합니다..."
    # Dockerfile은 이제 이 스크립트 기준으로 ../crop에 위치
    # 빌드 컨텍스트는 프로젝트 루트
    docker build -t $CROPPER_IMAGE_NAME -f "$PROJECT_ROOT/crop/cropper.Dockerfile" "$PROJECT_ROOT"
    if [ $? -ne 0 ]; then
        echo "Docker 빌드 실패. 종료합니다."
        exit 1
    fi
else
    echo "크로퍼 Docker 이미지를 찾았습니다. 빌드를 건너니다."
fi

echo "크로퍼 컨테이너를 실행합니다..."
# PROJECT_ROOT를 기준으로 절대 경로를 사용하여 볼륨 마운트
docker run --rm \
    -v "$(realpath "$HOST_WRITTEN_DIR")":/app/written \
    -v "$(realpath "$HOST_OUTPUT_DIR")":/app/cropped \
    -v "$(realpath "$HOST_DEBUG_DIR")":/app/debug_output \
    $CROPPER_IMAGE_NAME /app/glyph_cropper.py /app/written /app/cropped # 인자 전달 추가

# 실행 결과 확인
if [ $? -ne 0 ]; then
    echo "컨테이너 실행 중 크롭 작업 실패."
    exit 1
else
    echo "크롭 작업 완료."
    echo "  - 글리프: $HOST_OUTPUT_DIR"
    echo "  - 디버그 이미지: $HOST_DEBUG_DIR"
fi
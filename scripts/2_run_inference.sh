#!/bin/bash

set -e

# 인자 처리
if [ -z "$1" ]; then
    FONT_NAME="default_font_name"
    echo "폰트 이름이 주어지지 않았습니다. 기본값 'default_font_name'을 사용합니다."
else
    FONT_NAME="$1"
    echo "폰트 이름: '$FONT_NAME'을(를) 사용합니다."
fi

# 경로 설정
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST_PIPELINE_DIR="$PROJECT_ROOT"
IMAGE_NAME="fontory-inference"
CONTAINER_WORK_DIR="/app"
CONTAINER_REF_DIR="$CONTAINER_WORK_DIR/result/1_cropped"
CONTAINER_OUTPUT_DIR="$CONTAINER_WORK_DIR/result/2_inference"
BUILD_CONTEXT="$PROJECT_ROOT/inference"

# 입력 디렉토리 확인
if [ ! -d "$PROJECT_ROOT/result/1_cropped/$FONT_NAME" ]; then
  echo "오류: 참조 디렉토리 '$PROJECT_ROOT/result/1_cropped/$FONT_NAME'가 존재하지 않습니다."
  exit 1
fi

# Docker 이미지 빌드 (필요시)
if ! docker image inspect "$IMAGE_NAME":latest > /dev/null 2>&1; then
  echo "이미지 '$IMAGE_NAME:latest'를 찾을 수 없습니다. 컨텍스트 '$BUILD_CONTEXT'에서 빌드를 시작합니다..."
  docker build --no-cache -t "$IMAGE_NAME" -f "$BUILD_CONTEXT/Dockerfile" "$BUILD_CONTEXT"
else
  echo "이미지 '$IMAGE_NAME:latest'가 이미 존재합니다. 빌드를 건너뛰니다."
fi

# 출력 디렉토리 생성
mkdir -p "$PROJECT_ROOT/result/2_inference/$FONT_NAME"

echo "추론 컨테이너를 실행합니다..."
echo "Pipeline 마운트: $PROJECT_ROOT -> $CONTAINER_WORK_DIR"

# 컨테이너 실행
docker run \
  --gpus all \
  --rm \
  --shm-size=16gb \
  -v "$PROJECT_ROOT":"$CONTAINER_WORK_DIR" \
  -e PYTHONPATH="$CONTAINER_WORK_DIR:$CONTAINER_WORK_DIR/inference/resources:$CONTAINER_WORK_DIR/resources:/app/resource" \
  -e PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:32 \
  "$IMAGE_NAME" \
  --reference_dir "$CONTAINER_REF_DIR" \
  --output_dir "$CONTAINER_OUTPUT_DIR" \
  --font_name "$FONT_NAME"

echo "추론 완료. 출력은 '$PROJECT_ROOT/result/2_inference/$FONT_NAME'에 저장되어야 합니다."
#!/bin/bash

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST_PIPELINE_DIR="$PROJECT_ROOT"

IMAGE_NAME="inference-step"
CONTAINER_WORK_DIR="/app"

CONTAINER_REF_DIR="$CONTAINER_WORK_DIR/result/1_cropped"
CONTAINER_OUTPUT_DIR="$CONTAINER_WORK_DIR/result/2_inference"

BUILD_CONTEXT="$PROJECT_ROOT/inference"

if [ ! -d "$PROJECT_ROOT/result/1_cropped" ]; then
  echo "오류: 참조 디렉토리 '$PROJECT_ROOT/result/1_cropped'가 존재하지 않습니다."
  exit 1
fi

if ! docker image inspect "$IMAGE_NAME":latest > /dev/null 2>&1; then
  echo "이미지 '$IMAGE_NAME:latest'를 찾을 수 없습니다. 컨텍스트 '$BUILD_CONTEXT'에서 빌드를 시작합니다..."
  docker build --no-cache -t "$IMAGE_NAME" -f "$BUILD_CONTEXT/Dockerfile" "$BUILD_CONTEXT"
else
  echo "이미지 '$IMAGE_NAME:latest'가 이미 존재합니다. 빌드를 건너뛰니다."
fi

mkdir -p "$PROJECT_ROOT/result/2_inference"

echo "추론 컨테이너를 실행합니다..."
echo "Pipeline 마운트: $PROJECT_ROOT -> $CONTAINER_WORK_DIR"

docker run \
  --gpus all \
  --rm \
  --shm-size=16gb \
  -v "$PROJECT_ROOT":"$CONTAINER_WORK_DIR" \
  -e PYTHONPATH="$CONTAINER_WORK_DIR:$CONTAINER_WORK_DIR/inference/resources:$CONTAINER_WORK_DIR/resources:/app/resource" \
  -e PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:32 \
  "$IMAGE_NAME" \
  --reference_dir "$CONTAINER_REF_DIR" \
  --output_dir "$CONTAINER_OUTPUT_DIR"

echo "추론 완료. 출력은 '$PROJECT_ROOT/result/2_inference'에 저장되어야 합니다."
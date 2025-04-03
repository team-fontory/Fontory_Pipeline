#!/bin/bash

# JPG를 SVG로 변환하는 Docker 컨테이너를 빌드하고 실행하는 스크립트

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
IMAGE_NAME="fontory-jpg2svg"
PROJECT_ROOT=$(dirname "$0")/..
BUILD_CONTEXT="$PROJECT_ROOT/jpg2svg"
HOST_INPUT_DIR="$PROJECT_ROOT/result/2_inference/$FONT_NAME"
HOST_OUTPUT_DIR="$PROJECT_ROOT/result/3_svg/$FONT_NAME"
CONTAINER_INPUT_DIR="/app/input_jpg"
CONTAINER_OUTPUT_DIR="/app/output_svg"

# 입력 디렉토리 확인
if [ ! -d "$HOST_INPUT_DIR" ]; then
  echo "오류: 입력 디렉토리 '$HOST_INPUT_DIR'를 찾을 수 없습니다."
  echo "'inference' 단계가 성공적으로 실행되었는지 확인하세요."
  exit 1
fi

# 출력 디렉토리 생성
mkdir -p "$HOST_OUTPUT_DIR"

# Docker 이미지 빌드 (필요시)
if ! docker image inspect "$IMAGE_NAME":latest > /dev/null 2>&1; then
  echo "이미지 '$IMAGE_NAME:latest'를 찾을 수 없습니다. 컨텍스트 '$BUILD_CONTEXT'에서 빌드를 시작합니다..."
  docker build -t "$IMAGE_NAME" "$BUILD_CONTEXT"
else
  echo "이미지 '$IMAGE_NAME:latest'가 이미 존재합니다. 빌드를 건너뛰니다."
fi

echo "JPG to SVG 변환 컨테이너를 실행합니다..."
echo "  호스트 입력 디렉토리:  $HOST_INPUT_DIR"
echo "  호스트 출력 디렉토리: $HOST_OUTPUT_DIR"

# 컨테이너 실행
docker run --rm \
  -v "$(realpath "$HOST_INPUT_DIR")":"$CONTAINER_INPUT_DIR":ro \
  -v "$(realpath "$HOST_OUTPUT_DIR")":"$CONTAINER_OUTPUT_DIR" \
  "$IMAGE_NAME" \
  "$CONTAINER_INPUT_DIR" "$CONTAINER_OUTPUT_DIR"

echo "JPG to SVG 변환 완료. 출력은 '$HOST_OUTPUT_DIR'에 저장되어야 합니다." 
#!/bin/bash

# JPG를 SVG로 변환하는 Docker 컨테이너를 빌드하고 실행하는 스크립트

set -e # 오류 발생 시 즉시 종료

IMAGE_NAME="jpg2svg-converter" # Docker 이미지 이름
PROJECT_ROOT=$(dirname "$0")/.. # 스크립트가 ./pipeline/scripts에 있다고 가정
BUILD_CONTEXT="$PROJECT_ROOT/jpg2svg" # 빌드 컨텍스트 (Dockerfile 위치)
HOST_INPUT_DIR="$PROJECT_ROOT/result/2_inference/default_font_name"  # 이전 단계(크롭)의 입력 디렉토리
HOST_OUTPUT_DIR="$PROJECT_ROOT/result/3_svg" # 이 단계의 출력 디렉토리
CONTAINER_INPUT_DIR="/app/input_jpg" # 컨테이너 내 입력 디렉토리
CONTAINER_OUTPUT_DIR="/app/output_svg" # 컨테이너 내 출력 디렉토리

# 입력 디렉토리가 존재하는지 확인
if [ ! -d "$HOST_INPUT_DIR" ]; then
  echo "오류: 입력 디렉토리 '$HOST_INPUT_DIR'를 찾을 수 없습니다."
  echo "'crop' 단계가 성공적으로 실행되었는지 확인하세요."
  exit 1
fi

# 호스트에 출력 디렉토리가 존재하는지 확인하고 없으면 생성
mkdir -p "$HOST_OUTPUT_DIR"

# 이미지가 이미 존재하는지 확인
if ! docker image inspect "$IMAGE_NAME":latest > /dev/null 2>&1; then
  echo "이미지 '$IMAGE_NAME:latest'를 찾을 수 없습니다. 컨텍스트 '$BUILD_CONTEXT'에서 빌드를 시작합니다..."
  docker build -t "$IMAGE_NAME" "$BUILD_CONTEXT"
else
  echo "이미지 '$IMAGE_NAME:latest'가 이미 존재합니다. 빌드를 건너뛰니다."
fi

echo "JPG to SVG 변환 컨테이너를 실행합니다..."
echo "  호스트 입력 디렉토리:  $HOST_INPUT_DIR"
echo "  호스트 출력 디렉토리: $HOST_OUTPUT_DIR"

# 컨테이너 실행, 입력 및 출력 매핑, 인자 전달
docker run --rm \
  -v "$(realpath "$HOST_INPUT_DIR")":"$CONTAINER_INPUT_DIR":ro \
  -v "$(realpath "$HOST_OUTPUT_DIR")":"$CONTAINER_OUTPUT_DIR" \
  "$IMAGE_NAME" \
  "$CONTAINER_INPUT_DIR" "$CONTAINER_OUTPUT_DIR" # ENTRYPOINT가 스크립트를 실행한다고 가정하고 인자만 전달

echo "JPG to SVG 변환 완료. 출력은 '$HOST_OUTPUT_DIR'에 저장되어야 합니다." 
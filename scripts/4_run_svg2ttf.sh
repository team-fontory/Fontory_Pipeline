#!/bin/bash

# SVG를 TTF 및 WOFF로 변환하는 Docker 컨테이너를 실행하는 스크립트

set -e # 오류 발생 시 즉시 종료

# --- 기본값 설정 ---
FONT_NAME="" # 폰트 이름 (필수 인자)
FAMILY_NAME="" # 폰트 패밀리 이름 (기본값은 FONT_NAME 기반으로 설정됨)
STYLE_NAME="Regular" # 기본 폰트 스타일

# --- 이미지 및 고정 경로 ---
IMAGE_NAME="svg2ttf-converter" # 로컬에서 빌드할 Docker 이미지 이름
PROJECT_ROOT=$(dirname "$0")/.. # 스크립트가 ./pipeline/scripts에 있다고 가정
BUILD_CONTEXT="$PROJECT_ROOT/svg2ttf" # 빌드 컨텍스트 (Dockerfile 위치)
HOST_INPUT_DIR="$PROJECT_ROOT/result/3_svg"    # 이전 단계(jpg2svg)의 입력 디렉토리 (SVG 파일)
HOST_OUTPUT_DIR="$PROJECT_ROOT/result/4_fonts" # 이 단계의 출력 디렉토리 (TTF/WOFF 파일)
CONTAINER_INPUT_DIR="/app/input_svg" # 컨테이너 내 입력 디렉토리 (Dockerfile 기준)
CONTAINER_OUTPUT_DIR="/app/output_fonts" # 컨테이너 내 출력 디렉토리 (Dockerfile 기준)
# CONTAINER_SCRIPT_PATH="/app/svg_to_ttf_converter.py" # 스크립트는 이미지 내부에 있음

# 사용법 안내 함수
usage() {
  echo "사용법: $0 -f <폰트_이름> [-F <패밀리_이름>] [-S <스타일_이름>]"
  echo "  -f, --font-name       폰트 이름 (PostScript 이름, 필수, 공백 없음)"
  echo "  -F, --family-name     폰트 패밀리 이름 (기본값: '<폰트_이름> FONT')"
  echo "  -S, --style-name      폰트 스타일 이름 (기본값: '$STYLE_NAME')"
  echo "  -h, --help            이 도움말 메시지를 표시합니다"
  exit 1
}

# --- 스크립트 인자 처리 (getopt 사용) ---
TEMP=$(getopt -o hf:F:S: --long help,font-name:,family-name:,style-name: -n "$0" -- "$@")

if [ $? != 0 ]; then
  echo "인자 파싱 오류..." >&2
  usage
fi

eval set -- "$TEMP"

while true; do
  case "$1" in
    -f | --font-name ) FONT_NAME="$2"; shift 2 ;;
    -F | --family-name ) FAMILY_NAME="$2"; shift 2 ;;
    -S | --style-name ) STYLE_NAME="$2"; shift 2 ;;
    -h | --help ) usage ;;
    -- ) shift; break ;;
    * ) break ;;
  esac
done

# 필수 인자 확인
if [ -z "$FONT_NAME" ]; then
  echo "오류: 폰트 이름 (-f 또는 --font-name)은 필수입니다." >&2
  usage
fi

# 패밀리 이름 기본값 설정 (사용자가 -F 제공하지 않은 경우)
if [ -z "$FAMILY_NAME" ]; then
  FAMILY_NAME="${FONT_NAME} FONT"
fi

# 인자 처리 후 출력 파일 이름 및 경로 설정
OUTPUT_TTF_FILENAME="${FONT_NAME}.ttf" # 스타일 이름 제거
# 컨테이너 내 출력 TTF *기본* 경로 (파이썬 스크립트는 이를 기반으로 .ttf와 .woff 생성)
CONTAINER_OUTPUT_TTF_PATH="$CONTAINER_OUTPUT_DIR/$OUTPUT_TTF_FILENAME"

# --- 입력 유효성 검사 ---
if [ ! -d "$HOST_INPUT_DIR" ]; then
  echo "오류: 입력 SVG 디렉토리 '$HOST_INPUT_DIR'를 찾을 수 없습니다."
  echo "'jpg2svg' 단계가 성공적으로 실행되었는지 확인하세요."
  exit 1
fi

# --- 디렉토리 설정 ---
mkdir -p "$HOST_OUTPUT_DIR" # 호스트 출력 디렉토리 생성
if [ $? -ne 0 ]; then
  echo "오류: 출력 디렉토리 '$HOST_OUTPUT_DIR'를 생성할 수 없습니다." >&2
  exit 1
fi

# --- Docker 빌드 (필요시) ---
# 이미지가 이미 존재하는지 확인
if ! docker image inspect "$IMAGE_NAME":latest > /dev/null 2>&1; then
  echo "로컬 이미지 '$IMAGE_NAME:latest'를 찾을 수 없습니다. 컨텍스트 '$BUILD_CONTEXT'에서 빌드를 시작합니다..."
  docker build -t "$IMAGE_NAME" "$BUILD_CONTEXT"
else
  echo "로컬 이미지 '$IMAGE_NAME:latest'가 이미 존재합니다. 빌드를 건너뛰니다."
fi

# --- Docker 실행 ---
CONTAINER_NAME="fontforge-svg2ttf-$(date +%s)"
echo "SVG to TTF/WOFF 변환 컨테이너를 실행합니다..."
echo "  빌드된 이미지:          $IMAGE_NAME:latest"
echo "  입력 SVG 디렉토리 (호스트): $(realpath "$HOST_INPUT_DIR")"
echo "  출력 디렉토리 (호스트):   $(realpath "$HOST_OUTPUT_DIR")"
echo "  출력 기본 이름 (컨테이너): $OUTPUT_TTF_FILENAME"
echo "  폰트 이름:            $FONT_NAME"
echo "  패밀리 이름:         $FAMILY_NAME"
echo "  스타일 이름:          $STYLE_NAME"

# 컨테이너 실행, fontforge 스크립트에 인자 전달 (Dockerfile의 ENTRYPOINT/CMD 기준)
docker run --rm --name "$CONTAINER_NAME" \
  -v "$(realpath "$HOST_INPUT_DIR")":"$CONTAINER_INPUT_DIR":ro \
  -v "$(realpath "$HOST_OUTPUT_DIR")":"$CONTAINER_OUTPUT_DIR":rw \
  "$IMAGE_NAME" \
  "$CONTAINER_INPUT_DIR" \
  "$CONTAINER_OUTPUT_TTF_PATH" \
  "$FONT_NAME" \
  "$FAMILY_NAME" \
  "$STYLE_NAME"

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
  echo "---------------------------------"
  echo "폰트 생성 성공!"
  echo "출력 파일(.ttf, .woff)은 '$HOST_OUTPUT_DIR' 디렉토리에 저장되었습니다."
else
  echo "---------------------------------"
  echo "오류: 폰트 생성 실패 (종료 코드: $EXIT_CODE)." >&2
  echo "컨테이너 내부 오류 로그는 '$HOST_OUTPUT_DIR/fontforge_error.log' (생성된 경우) 또는"
  echo "컨테이너 로그를 확인하세요: docker logs $CONTAINER_NAME (오류 발생 시 컨테이너가 빠르게 삭제될 수 있음)."
  # 오류 로그 파일을 호스트로 복사 시도 (컨테이너가 이미 종료되었으면 실패할 수 있음)
  # docker cp "$CONTAINER_NAME":"/app/fontforge_error.log" "$HOST_OUTPUT_DIR/fontforge_error.log" 2>/dev/null || true
  exit $EXIT_CODE
fi

echo "--- SVG to TTF/WOFF 변환 완료 ---" 
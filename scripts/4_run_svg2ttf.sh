#!/bin/bash

# SVG를 TTF 및 WOFF로 변환하는 Docker 컨테이너를 실행하는 스크립트

set -e


# 인자 처리
if [ -z "$1" ]; then
    FONT_NAME="default_font_name"
    echo "폰트 이름이 주어지지 않았습니다. 기본값 'default_font_name'을 사용합니다."
else
    FONT_NAME="$1"
    echo "폰트 이름: '$FONT_NAME'을(를) 사용합니다."
fi

# 기본값 설정
FAMILY_NAME="${FONT_NAME} FAMILY"
STYLE_NAME="Regular"

# 이미지 및 경로 설정
IMAGE_NAME="fontory-svg2ttf"
PROJECT_ROOT=$(dirname "$0")/..
BUILD_CONTEXT="$PROJECT_ROOT/svg2ttf"
HOST_INPUT_DIR="$PROJECT_ROOT/result/3_svg/$FONT_NAME"
HOST_OUTPUT_DIR="$PROJECT_ROOT/result/4_fonts"
HOST_BASE_FONT="$PROJECT_ROOT/resource/NanumGothic.ttf"
CONTAINER_INPUT_DIR="/app/input_svg"
CONTAINER_OUTPUT_DIR="/app/output_fonts"
CONTAINER_BASE_FONT="/app/base_font.ttf"

# 사용법 안내 함수
usage() {
  echo "사용법: $0 -f <폰트_이름> [-F <패밀리_이름>] [-S <스타일_이름>]"
  echo "  -f, --font-name       폰트 이름 (PostScript 이름, 필수, 공백 없음)"
  echo "  -F, --family-name     폰트 패밀리 이름 (기본값: '<폰트_이름> FONT')"
  echo "  -S, --style-name      폰트 스타일 이름 (기본값: '$STYLE_NAME')"
  echo "  -h, --help            이 도움말 메시지를 표시합니다"
  exit 1
}

# 스크립트 인자 처리
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

# 입력 디렉토리 설정
HOST_INPUT_DIR="$PROJECT_ROOT/result/3_svg/$FONT_NAME"

# 출력 파일 경로 설정
OUTPUT_TTF_FILENAME="${FONT_NAME}.ttf"
CONTAINER_OUTPUT_TTF_PATH="$CONTAINER_OUTPUT_DIR/$OUTPUT_TTF_FILENAME"

# 입력 유효성 검사
if [ ! -d "$HOST_INPUT_DIR" ]; then
  echo "오류: 입력 SVG 디렉토리 '$HOST_INPUT_DIR'를 찾을 수 없습니다."
  echo "'jpg2svg' 단계가 성공적으로 실행되었는지 확인하세요."
  exit 1
fi
if [ ! -f "$HOST_BASE_FONT" ]; then
  echo "경고: 기본 폰트 파일 '$HOST_BASE_FONT'를 찾을 수 없습니다. 라틴 글리프 병합 없이 진행합니다."
fi

# 출력 디렉토리 생성
mkdir -p "$HOST_OUTPUT_DIR"
if [ $? -ne 0 ]; then
  echo "오류: 출력 디렉토리 '$HOST_OUTPUT_DIR'를 생성할 수 없습니다." >&2
  exit 1
fi

# Docker 이미지 빌드 (필요시)
if ! docker image inspect "$IMAGE_NAME":latest > /dev/null 2>&1; then
  echo "로컬 이미지 '$IMAGE_NAME:latest'를 찾을 수 없습니다. 컨텍스트 '$BUILD_CONTEXT'에서 빌드를 시작합니다..."
  docker build -t "$IMAGE_NAME" "$BUILD_CONTEXT"
else
  echo "로컬 이미지 '$IMAGE_NAME:latest'가 이미 존재합니다. 빌드를 건너뛰니다."
fi

# Docker 실행
CONTAINER_NAME="fontforge-svg2ttf-$(date +%s)"
echo "SVG to TTF/WOFF 변환 컨테이너를 실행합니다..."
echo "  빌드된 이미지:          $IMAGE_NAME:latest"
echo "  입력 SVG 디렉토리 (호스트): $(realpath "$HOST_INPUT_DIR")"
echo "  출력 디렉토리 (호스트):   $(realpath "$HOST_OUTPUT_DIR")"
echo "  출력 기본 이름 (컨테이너): $OUTPUT_TTF_FILENAME"
echo "  폰트 이름:            $FONT_NAME"
echo "  패밀리 이름:         $FAMILY_NAME"
echo "  스타일 이름:          $STYLE_NAME"
echo "  기본 폰트 (호스트):   $(realpath "$HOST_BASE_FONT" 2>/dev/null || echo "찾을 수 없음")"

docker run --rm --name "$CONTAINER_NAME" \
  -v "$(realpath "$HOST_INPUT_DIR")":"$CONTAINER_INPUT_DIR":ro \
  -v "$(realpath "$HOST_OUTPUT_DIR")":"$CONTAINER_OUTPUT_DIR":rw \
  -v "$(realpath "$HOST_BASE_FONT")":"$CONTAINER_BASE_FONT":ro \
  "$IMAGE_NAME" \
  "$CONTAINER_INPUT_DIR" \
  "$CONTAINER_OUTPUT_TTF_PATH" \
  "$FONT_NAME" \
  "$FAMILY_NAME" \
  "$STYLE_NAME" \
  "$CONTAINER_BASE_FONT"

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
  exit $EXIT_CODE
fi

echo "--- SVG to TTF/WOFF 변환 완료 ---" 
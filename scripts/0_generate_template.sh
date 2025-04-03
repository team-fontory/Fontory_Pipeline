#!/bin/bash

# Docker를 사용하여 템플릿 페이지를 생성하는 스크립트

GENERATOR_IMAGE_NAME="fontory-template-generator"
PROJECT_ROOT=$(dirname "$0")/..
HOST_OUTPUT_DIR="$PROJECT_ROOT/result/0_template"

# 출력 디렉토리 생성
mkdir -p "$HOST_OUTPUT_DIR"

# Docker 이미지 빌드 (필요시)
if ! docker image inspect $GENERATOR_IMAGE_NAME > /dev/null 2>&1; then
    echo "생성기 Docker 이미지를 찾을 수 없습니다. 빌드를 시작합니다..."
    docker build -t $GENERATOR_IMAGE_NAME -f "$PROJECT_ROOT/make_template/template.Dockerfile" "$PROJECT_ROOT"
    if [ $? -ne 0 ]; then
        echo "Docker 빌드 실패. 종료합니다."
        exit 1
    fi
else
    echo "생성기 Docker 이미지를 찾았습니다. 빌드를 건너뜁니다."
fi

echo "템플릿 생성기 컨테이너를 실행합니다..."

# 컨테이너 실행
docker run --rm \
    -v "$HOST_OUTPUT_DIR":/app/output_templates \
    $GENERATOR_IMAGE_NAME \
    sh -c "python /app/template_generator.py && echo '--- 컨테이너 내 /app/output_templates 목록: ---' && ls -al /app/output_templates"

COMMAND_EXIT_CODE=$?

# 실행 결과 확인
if [ $COMMAND_EXIT_CODE -ne 0 ]; then
    echo "컨테이너 실행 중 템플릿 생성 실패 (종료 코드: $COMMAND_EXIT_CODE)."
    exit 1
else
    echo "템플릿 생성 명령이 성공적으로 완료되었습니다. '$HOST_OUTPUT_DIR' 디렉토리를 확인하세요."
fi
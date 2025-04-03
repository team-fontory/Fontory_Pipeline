#!/bin/bash

# Docker를 사용하여 템플릿 페이지를 생성하는 스크립트

GENERATOR_IMAGE_NAME="fontory-template-generator" # 생성기 Docker 이미지 이름
PROJECT_ROOT=$(dirname "$0")/.. # 프로젝트 루트 디렉토리 (스크립트 위치 기준)
HOST_OUTPUT_DIR="$PROJECT_ROOT/result/0_template" # 호스트 결과 출력 디렉토리

# 호스트에 출력 디렉토리가 존재하는지 확인하고 없으면 생성
mkdir -p "$HOST_OUTPUT_DIR"

# Docker 이미지가 이미 존재하는지 확인
if ! docker image inspect $GENERATOR_IMAGE_NAME > /dev/null 2>&1; then
    echo "생성기 Docker 이미지를 찾을 수 없습니다. 빌드를 시작합니다..."
    # ../make_template 안의 Dockerfile을 사용하여 이미지 빌드
    # 빌드 컨텍스트는 프로젝트 루트
    docker build -t $GENERATOR_IMAGE_NAME -f "$PROJECT_ROOT/make_template/template.Dockerfile" "$PROJECT_ROOT"
    if [ $? -ne 0 ]; then
        echo "Docker 빌드 실패. 종료합니다."
        exit 1
    fi
else
    echo "생성기 Docker 이미지를 찾았습니다. 빌드를 건너뜁니다."
fi

echo "템플릿 생성기 컨테이너를 실행합니다..."
# 컨테이너 실행, 출력 디렉토리 마운트
# CMD를 오버라이드하여 스크립트 실행 후 컨테이너 내 출력 디렉토리 목록 표시
docker run --rm \
    -v "$HOST_OUTPUT_DIR":/app/output_templates \
    $GENERATOR_IMAGE_NAME \
    sh -c "python /app/template_generator.py && echo '--- 컨테이너 내 /app/output_templates 목록: ---' && ls -al /app/output_templates"

COMMAND_EXIT_CODE=$? # 컨테이너 실행 종료 코드 저장

# 실행 결과 확인
if [ $COMMAND_EXIT_CODE -ne 0 ]; then
    echo "컨테이너 실행 중 템플릿 생성 실패 (종료 코드: $COMMAND_EXIT_CODE)."
    exit 1
else
    echo "템플릿 생성 명령이 성공적으로 완료되었습니다. '$HOST_OUTPUT_DIR' 디렉토리를 확인하세요."
fi

# 필요시 원래 디렉토리로 돌아감 (주석 처리됨)
# cd -
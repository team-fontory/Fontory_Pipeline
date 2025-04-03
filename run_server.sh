#!/bin/bash

# 디버깅을 위한 셸 스크립트 옵션 설정
set -e
set -x

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT=$(dirname "$0")
cd "$PROJECT_ROOT"

# 로그 및 결과 디렉토리 확인 및 생성
LOG_DIR="./log"
RESULT_DIR="./result"
mkdir -p $LOG_DIR
mkdir -p $RESULT_DIR/0_template
mkdir -p $RESULT_DIR/1_cropped
mkdir -p $RESULT_DIR/2_inference
mkdir -p $RESULT_DIR/3_svg
mkdir -p $RESULT_DIR/4_fonts
mkdir -p ./written
echo "로그 및 결과 디렉토리 확인/생성 완료"

# 로그 디렉토리 권한 확보 및 기존 로그 파일 정리
echo "로그 디렉토리 권한 확인 및 정리..."
chmod u+w $LOG_DIR || echo "경고: 로그 디렉토리 권한 변경 실패. 계속 진행합니다."
ls $LOG_DIR/*.log 2>/dev/null | while read -r logfile; do
    echo "기존 로그 파일 삭제 시도: $logfile"
    rm -f "$logfile" || echo "경고: 로그 파일 '$logfile' 삭제 실패. 권한 문제일 수 있습니다."
done

# 스크립트에 실행 권한 부여
chmod +x ./scripts/*.sh
echo "스크립트에 실행 권한 부여됨"

# 파이썬 가상 환경 설정
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "가상 환경 생성 중: $VENV_DIR"
    python3 -m venv $VENV_DIR
    echo "가상 환경 생성됨"
else
    echo "가상 환경 이미 존재함: $VENV_DIR"
fi

# 가상 환경 활성화
source "$VENV_DIR/bin/activate"
echo "가상 환경 활성화됨"

# 필요한 패키지 설치
echo "필요한 패키지 설치 중 (requirements.txt)..."
pip install -r requirements.txt

# API 서버 실행
echo "FastAPI 서버 실행 중 (uvicorn)..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload 
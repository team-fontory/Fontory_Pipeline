#!/bin/bash

# FastAPI 서버 (uvicorn) 프로세스를 찾아 종료하는 스크립트

set -x

PROCESS_NAME="uvicorn main:app"

echo "FastAPI 서버 프로세스 ('$PROCESS_NAME') 찾는 중..."

# pgrep으로 프로세스 ID 찾기
PIDS=$(pgrep -f "$PROCESS_NAME")

if [ -z "$PIDS" ]; then
  echo "실행 중인 FastAPI 서버 프로세스를 찾을 수 없습니다."
  exit 0
fi

echo "찾은 프로세스 ID: $PIDS"

# 프로세스 종료
kill $PIDS

sleep 1

# 종료 확인
if pgrep -f "$PROCESS_NAME" > /dev/null; then
  echo "오류: 서버 프로세스를 종료하지 못했습니다. 강제 종료 시도 (-9)..."
  kill -9 $PIDS
  sleep 1
  if pgrep -f "$PROCESS_NAME" > /dev/null; then
    echo "오류: 서버 프로세스를 강제로 종료하지 못했습니다."
    exit 1
  else
    echo "서버 프로세스를 강제로 종료했습니다."
  fi
else
  echo "서버 프로세스를 성공적으로 종료했습니다."
fi

exit 0 
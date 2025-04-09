#!/bin/bash

# Prometheus, Loki 종료
docker compose -f ./fastAPI/prometheus_loki/compose.yml down

# 포트 8000을 사용 중인 프로세스를 찾아 종료하는 스크립트

set -x

PORT=8000

echo "포트 $PORT 를 사용하는 프로세스를 찾는 중..."

# lsof를 사용하여 포트 8000을 사용 중인 프로세스의 PID 찾기
PIDS=$(lsof -t -i :$PORT)

if [ -z "$PIDS" ]; then
  echo "포트 $PORT 를 사용하는 프로세스를 찾을 수 없습니다."
  exit 0
fi

echo "찾은 프로세스 ID: $PIDS"

# 프로세스 종료
kill $PIDS

sleep 1

# 종료 확인
if lsof -t -i :$PORT > /dev/null; then
  echo "오류: 포트 $PORT 를 사용하는 프로세스를 종료하지 못했습니다. 강제 종료 시도 (-9)..."
  kill -9 $PIDS
  sleep 1
  if lsof -t -i :$PORT > /dev/null; then
    echo "오류: 포트 $PORT 를 사용하는 프로세스를 강제로 종료하지 못했습니다."
    exit 1
  else
    echo "포트 $PORT 를 사용하는 프로세스를 강제로 종료했습니다."
  fi
else
  echo "포트 $PORT 를 사용하는 프로세스를 성공적으로 종료했습니다."
fi

exit 0
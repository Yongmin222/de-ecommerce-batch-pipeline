#!/bin/bash
set -e

# 호스트에서 마운트된 docker.sock의 소유 그룹 번호(GID)를 확인
DOCKER_GID=$(stat -c '%g' /var/run/docker.sock)

# 컨테이너 안 docker 그룹이 이미 그 번호를 쓰고 있는지 확인
if ! getent group "$DOCKER_GID" > /dev/null 2>&1; then
    groupadd -g "$DOCKER_GID" docker_host
    usermod -aG docker_host airflow
fi

# airflow 사용자 권한으로 원래 실행하려던 명령어 이어서 실행
exec /entrypoint "$@"

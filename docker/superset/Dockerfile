FROM apache/superset:latest

USER root

# mysqlclient 컴파일에 필요한 시스템 패키지
RUN apt-get update && \
    apt-get install -y pkg-config default-libmysqlclient-dev build-essential && \
    rm -rf /var/lib/apt/lists/*

# Superset은 /app/.venv 라는 별도 가상환경을 쓰므로, uv로 그 경로를 명시해서 설치
RUN uv pip install --python /app/.venv/bin/python \
    pymysql psycopg2-binary mysqlclient

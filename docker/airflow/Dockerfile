FROM apache/airflow:2.9.3

USER root

# docker CLI 설치 (Docker-in-Docker로 Spark 컨테이너 제어)
RUN apt-get update && \
    apt-get install -y docker.io && \
    rm -rf /var/lib/apt/lists/*

# 우리가 만든 entrypoint 스크립트를 이미지 안으로 복사
COPY entrypoint.sh /entrypoint-custom.sh
RUN chmod +x /entrypoint-custom.sh

USER airflow

# MySQL 접속용 드라이버
RUN pip install --no-cache-dir pymysql

USER root
ENTRYPOINT ["/entrypoint-custom.sh"]

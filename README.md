# 이커머스 배치 데이터 파이프라인

Kaggle 이커머스(화장품 쇼핑몰) 이벤트 로그를 정제 → 적재 → 집계 → 자동화 → 시각화하는 배치 파이프라인입니다. NAVER 클라우드 서버 위에 Docker Compose로 전체 인프라를 구성했습니다.

## 아키텍처

```
Kaggle CSV → 정제(Pandas) → 적재(MySQL) → 집계(Spark) → 자동화(Airflow) → 시각화(Superset)
```

| 단계 | 역할 | 기술 |
|---|---|---|
| 정제 | 결측치/이상치 처리, 타입 변환 | Pandas |
| 적재 | 정제된 데이터 저장 | MySQL 8.0 |
| 집계 | 일별 매출, 브랜드별 조회수 집계 (Master+Worker 2 클러스터) | Apache Spark 4.0 |
| 자동화 | 매일 새벽 2시 전체 파이프라인 자동 실행 | Apache Airflow 2.9.3 |
| 시각화 | 집계 결과 대시보드 | Apache Superset |

모든 서비스는 Docker Compose로 관리되며, 전용 Dockerfile을 통해 재현 가능하게 구성했습니다.

## 데이터 준비

1. [Kaggle: eCommerce Events History in Cosmetics Shop](https://www.kaggle.com/datasets/mkechinov/ecommerce-events-history-in-cosmetics-shop) 에서 `2019-Oct.csv` 다운로드
2. 프로젝트 루트에 `data/` 폴더를 만들고 그 안에 저장

## 실행 방법

```bash
# 1. 필요한 폴더 및 권한 설정
mkdir -p dags logs plugins data mysql-data
echo "AIRFLOW_UID=50000" > .env
chown -R 50000:50000 dags logs plugins

# 2. 전체 스택 빌드 및 실행
docker compose up -d --build

# 3. 웹 UI 접속 (클라우드 방화벽으로 포트가 막혀있다면 SSH 터널 필요)
# Spark Master UI:  http://localhost:8080
# Airflow:          http://localhost:8081  (admin / admin)
# Superset:         http://localhost:8088  (admin / admin)
```

Airflow 웹 화면에서 `ecommerce_batch_pipeline` DAG를 Active로 전환하면 매일 새벽 2시에 자동 실행되며, ▶ 버튼으로 즉시 실행도 가능합니다.

## 프로젝트 구조

```
.
├── docker-compose.yml          # 전체 서비스 정의 (MySQL, Spark, Airflow, Superset)
├── docker/
│   ├── spark/Dockerfile        # MySQL JDBC 드라이버 내장
│   ├── airflow/
│   │   ├── Dockerfile          # docker CLI, pymysql 설치
│   │   └── entrypoint.sh       # 호스트 docker 그룹 GID 자동 매핑
│   └── superset/
│       ├── Dockerfile          # pymysql, psycopg2, mysqlclient 설치
│       └── superset_config.py  # PostgreSQL 메타데이터 DB 연결 설정
├── scripts/
│   ├── clean_and_load.py       # 정제 + MySQL 적재
│   └── aggregate.py            # Spark 집계 + 결과 재저장
└── dags/
    └── ecommerce_pipeline.py   # Airflow DAG 정의
```

## 데이터 정제 기준

| 컬럼 | 결측 비율 | 처리 |
|---|---|---|
| `category_code` | 98.4% | 대부분 결측이라 채우지 않고, `has_category` 플래그 컬럼만 추가 |
| `brand` | 40.4% | "Unknown"으로 채움 |
| `user_session` | 0.02% | 결측 행 제거 |
| `price` | - | 음수값(오류 데이터) 20건 제거 |

## 겪은 문제와 해결

- **Bitnami 이미지 카탈로그 이전**: 2025년 8월 Bitnami가 무료 이미지 배포를 축소하며 `bitnami/*` → `bitnamilegacy/*`로 저장소가 이전됨. 이미지 태그를 `bitnamilegacy/spark:latest`로 변경해 대응
- **Java 버전 불일치**: Spark 4.0은 Java 17 요구, 서버 기본은 Java 8 → Java 17 별도 설치 및 전환
- **Docker-in-Docker 권한**: Airflow 컨테이너 안에서 `docker` 명령어로 Spark 컨테이너를 제어하려면 호스트의 docker 소켓을 공유해야 하는데, 컨테이너 안 `docker` 그룹 GID가 호스트와 달라 권한 오류 발생 → entrypoint 스크립트로 컨테이너 시작 시 GID를 자동으로 맞추도록 처리
- **JDBC 대용량 읽기 메모리 부족**: Spark Executor 메모리 기본값(1GB)으로 410만 행을 한 번에 읽다 `OutOfMemoryError` 발생 → `spark.executor.memory` 명시적 조정으로 해결
- **데이터 중복 적재**: `clean_and_load.py`가 CSV 원본을 매번 재정제하는 구조인데 MySQL 저장 옵션이 `append`였던 탓에, Airflow 재시도 과정에서 같은 데이터가 10배로 누적됨 → `replace` 모드로 변경
- **Python 가상환경 경로 불일치**: Superset 컨테이너는 `/app/.venv`라는 별도 가상환경을 쓰는데, 일반 `pip install`은 이 경로 밖에 설치되어 실제 실행 환경이 인식하지 못함 → `uv pip install --python /app/.venv/bin/python`으로 정확한 경로 지정

## 데이터 인사이트

- 일별 매출은 3만~4만6천 사이를 오가며, 특히 토요일에 뚜렷하게 하락하는 패턴 확인 (주중 소비가 더 활발)
- 브랜드별 조회수는 상위 브랜드(runail)가 하위권 브랜드보다 3배 이상 높은 쏠림 현상을 보임

## 다음 계획

- 실시간 스트리밍 파이프라인(Kafka + Spark Structured Streaming) 별도 프로젝트로 진행 예정
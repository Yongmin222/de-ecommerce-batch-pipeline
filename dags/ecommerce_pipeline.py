from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    'owner': 'airflow',
    'retries': 1,
}

with DAG(
    dag_id='ecommerce_batch_pipeline',
    default_args=default_args,
    description='정제-적재-집계 배치 파이프라인',
    schedule_interval='0 2 * * *',
    start_date=datetime(2026, 9, 17),
    catchup=False,
    tags=['de-portfolio'],
) as dag:

    clean_and_load = BashOperator(
        task_id='clean_and_load',
        bash_command='python /opt/airflow/scripts/clean_and_load.py'
    )

    copy_aggregate_script = BashOperator(
        task_id='copy_aggregate_script',
	bash_command='docker cp /opt/airflow/scripts/aggregate.py spark-master:/opt/bitnami/spark/aggregate.py'
    )

    run_aggregate = BashOperator(
        task_id='run_aggregate',
        bash_command='docker exec -e JAVA_TOOL_OPTIONS="-Duser.home=/tmp" spark-master spark-submit /opt/bitnami/spark/aggregate.py'
    )

    clean_and_load >> copy_aggregate_script >> run_aggregate

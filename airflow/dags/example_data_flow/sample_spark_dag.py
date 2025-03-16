from datetime import datetime

from spark_jobs.sample_spark_job import run_sample_etl_job

from airflow.decorators import dag, task


# 일단 예제라서 이대로 두지만 실제로는 annotation 사용은 자제하라는 멘토님의 피드백이 있었음에 주의
@dag(
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["spark", "connect"],
)
def spark_connect_etl_dag():
    @task
    def execute_spark_job():
        run_sample_etl_job()

    execute_spark_job()


spark_connect_etl_dag = spark_connect_etl_dag()

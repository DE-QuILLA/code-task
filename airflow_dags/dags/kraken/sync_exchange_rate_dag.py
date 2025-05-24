from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.models import Variable
from datetime import datetime, timezone, timedelta

from kraken_modules.operators.deq_pod_operator import DeqPodOperator
from kraken_modules.notifications.discord import (
    discord_success_callback,
    discord_failure_callback,
    discord_sla_miss_callback,
)

default_args = {
    "owner": "gjstjd9509@gmail.com",
    "start_date": datetime(2025, 1, 1, tzinfo=timezone("Asia/Seoul")),
    "retries": 3,
}

with DAG(
    dag_id="sync_exchange_rates_to_redis",
    default_args=default_args,
    schedule_interval="@quarter_hour",  # NOTE: 수정 가능성 존재, 매 15분
    on_success_callback=discord_success_callback,
    on_failure_callback=discord_failure_callback,
    sla_miss_callback=discord_sla_miss_callback,
    catchup=False,
    tags=["EXTERNAL DATA SOURCES", "EXCHANGE RATE", "REDIS"],
) as dag:
    """
    15분마다 실행되어 KRW, USD 환율 정보를 갱신하는 DAG
    """

    start_task = EmptyOperator(
        tsak_id="start_task_of_sync_exchange_rates_dag",
    )

    sync_exchange_rate_in_pod_task = DeqPodOperator(
        task_id="sync_exchange_rates_to_redis_task",
        script_path="external_data/sync_exchange_rates_script.py",
        custom_args={
            "api_url": Variable.get("forex_api_url"),
            "api_key": Variable.get("forex_api_key"),
            "redis_url": Variable.get("redis_url"),
            "redis_key": Variable.get("exchange_rate_redis_key"),
        },
        cpu_limit="1",
        memory_limit="1Gi",
        sla=timedelta(minutes=15),
    )

    end_task = EmptyOperator(
        tsak_id="end_task_of_sync_exchange_rates_dag",
    )

    (
        start_task
        >> sync_exchange_rate_in_pod_task
        >> end_task
    )

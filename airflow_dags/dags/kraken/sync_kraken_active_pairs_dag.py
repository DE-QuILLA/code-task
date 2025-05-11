from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.models import Variable
from datetime import datetime, timezone, timedelta
from kraken_modules.operators.deq_pod_operator import DeqPodOperator
from kraken_modules.notifications.discord import discord_success_callback, discord_failure_callback, discord_sla_miss_callback

default_args = {
    "owner": "gjstjd9509@gmail.com",
    "start_date": datetime(2025, 1, 1, tzinfo=timezone('Asia/Seoul')),
    "retries": 3,
}

with DAG(
    dag_id="sync_kraken_active_pairs_to_redis",
    default_args=default_args,
    schedule_interval="",
    on_success_callback=discord_success_callback,
    on_failure_callback=discord_failure_callback,
    sla_miss_callback=discord_sla_miss_callback,
    catchup=False,
    tags=["example"],
) as dag:
    """
    Kraken REST api에서 활성 거래쌍 목록을 가져와서 redis에 저장하는 대그
    """

    start_task = EmptyOperator(
        tsak_id="start_sync_kraken_active_pairs_task",
    )

    sync_active_pairs_data_in_pod_task = DeqPodOperator(
        task_id="sync_kraken_active_pairs_to_redis",
        script_path="kraken/sync_kraken_active_pairs_script.py",
        custom_args={
            "api_url": Variable.get("kraken_api_url"),
            "redis_url": Variable.get("redis_url"),
            "redis_key": "kraken:active_pairs",
            "producer_url": Variable.get("kraken_producer_url"),
            "parmas": {},
            "headers": {},
            "retry_num": 5,
            "retry_delay": 5,
            "timeout": 120,
        },
        cpu_limit="1",
        memory_limit="1Gi",
        sla=timedelta(minutes=15),
    )

    end_task = EmptyOperator(
        tsak_id="end_sync_kraken_active_pairs_task",
    )

    start_task >> sync_active_pairs_data_in_pod_task >> end_task

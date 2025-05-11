from airflow.models import Variable
from tenacity import retry, stop_after_attempt, wait_fixed
from typing import Dict, Any
from kraken_modules.consts.time_consts import NOW_KST, NOW_UTC
import requests

# airflow 알림 채널 훅 URL
DISCORD_WEBHOOK = Variable.get("airflow_notification_discord_webhook_url")

# 5초 대기, 3회 재시도
@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def notify_discord(message: str, webhook_url: str):
    payload = {
        "content": message,
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(webhook_url, json=payload, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Discord 알림 실패: {e}")

def discord_success_callback(context: Dict[str, Any]):
    dag_id = context["dag"].dag_id
    run_id = context["run_id"]
    message = f"""
    --------------------------------
    ✅ DAG 성공: `{dag_id}`
    Run ID: `{run_id}`
    현재 UTC 시각: {NOW_UTC}
    현재 KST 시각: {NOW_KST}
    """
    notify_discord(message, DISCORD_WEBHOOK)

def discord_failure_callback(context: Dict[str, Any]):
    dag_id = context["dag"].dag_id
    run_id = context["run_id"]
    message = f"""
    --------------------------------
    ❌ DAG 실패: `{dag_id}`
    Run ID: `{run_id}`
    현재 UTC 시각: {NOW_UTC}
    현재 KST 시각: {NOW_KST}
    """
    notify_discord(message, DISCORD_WEBHOOK)

def discord_sla_miss_callback(context: Dict[str, Any]):
    dag_id = context["dag"].dag_id
    task_id = context["task_instance"].task_id
    run_id = context["run_id"]
    message = f"""
    --------------------------------
    ❌ SLA 실패 발생: `{dag_id}`.`{task_id}`
    Run ID: `{run_id}`
    현재 UTC 시각: {NOW_UTC}
    현재 KST 시각: {NOW_KST}
    """
    notify_discord(message, DISCORD_WEBHOOK)

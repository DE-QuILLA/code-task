from airflow.models import Variable
from tenacity import retry, stop_after_attempt, wait_fixed
from typing import Dict, Any, Optional
from kraken_modules.consts.time_consts import get_now_times
import requests
import logging

# airflow 알림 채널 훅 URL
DISCORD_WEBHOOK = Variable.get("AIRFLOW_ALERT_DISCORD_WEBHOOK_URL")


# if else문 줄여 가독성 향상 위한 logging.Logger 없을 시의 폴백용 단순 print 동작 클래스
class StdoutFallBackLogger:
    def info(self, message):
        print(message)

    def exception(self, message):
        print(message)


# 5초 대기, 3회 재시도
@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def notify_discord(kind_of_callback: str, message: str, webhook_url: str, logger: Optional[logging.Logger],):
    logger = logger or StdoutFallBackLogger()
    payload = {
        "content": message,
    }
    headers = {"Content-Type": "application/json"}
    try:
        logger.info(f"[Discord Webhook Notifier] 디스코드로 [{kind_of_callback}] 메시지 전송 시도!")
        response = requests.post(webhook_url, json=payload, headers=headers)
        response.raise_for_status()
        logger.info(f"[Discord Webhook Notifier] 디스코드로 [{kind_of_callback}] 메시지 전송 완료!")
    except Exception as e:
        logger.exception(f"[Discord Webhook Notifier] 디스코드로 [{kind_of_callback}] 메시지 전송 실패!")
        raise e


def discord_success_callback(context: Dict[str, Any]):
    ti = context["ti"]
    dag_id = context["dag"].dag_id
    run_id = context["run_id"]
    now_kst, now_utc = get_now_times()
    message = f"""
    --------------------------------
    ✅ DAG 성공: `{dag_id}`
    Run ID: `{run_id}`
    현재 UTC 시각: {now_utc}
    현재 KST 시각: {now_kst}
    """
    notify_discord(kind_of_callback=f"{dag_id} DAG SUCCESS", message=message, webhook_url=DISCORD_WEBHOOK, logger=ti.log,)


def discord_failure_callback(context: Dict[str, Any]):
    ti = context["ti"]
    dag_id = context["dag"].dag_id
    run_id = context["run_id"]
    now_kst, now_utc = get_now_times()
    message = f"""
    --------------------------------
    ❌ DAG 실패: `{dag_id}`
    Run ID: `{run_id}`
    현재 UTC 시각: {now_utc}
    현재 KST 시각: {now_kst}
    """
    notify_discord(kind_of_callback=f"{dag_id} DAG FAILURE", message=message, webhook_url=DISCORD_WEBHOOK, logger=ti.log,)


def discord_sla_miss_callback(context: Dict[str, Any]):
    ti = context["ti"]
    dag_id = context["dag"].dag_id
    task_id = context["task_instance"].task_id
    run_id = context["run_id"]
    now_kst, now_utc = get_now_times()
    message = f"""
    --------------------------------
    ❌ SLA 실패 발생: `{dag_id}`.`{task_id}`
    Run ID: `{run_id}`
    현재 UTC 시각: {now_utc}
    현재 KST 시각: {now_kst}
    """
    notify_discord(kind_of_callback=f"{dag_id} DAG SLA MISS", message=message, webhook_url=DISCORD_WEBHOOK, logger=ti.log,)

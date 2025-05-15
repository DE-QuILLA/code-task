from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import pendulum

# 현재 시각 상수
# NOTE: import할 당시의 시간으로 결정됨
NOW_KST = pendulum.now("Asia/Seoul")
NOW_UTC = datetime.now(ZoneInfo("UTC"))

# 함수 실행으로 코드 실행 당시의 시간 반환
def get_now_times():
    """실행 시 KST, UTC 시간 반환"""
    return (pendulum.now("Asia/Seoul"), datetime.now(ZoneInfo("UTC")))

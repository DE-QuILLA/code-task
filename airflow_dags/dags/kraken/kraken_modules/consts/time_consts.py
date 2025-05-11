from datetime import datetime, timezone
import pendulum

# 현재 시각 상수
NOW_KST = pendulum.now("Asia/Seoul")
NOW_UTC = datetime.now(timezone.utc)

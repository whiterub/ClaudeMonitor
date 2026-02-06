from datetime import datetime, timezone
from typing import Optional


def get_usage_color(utilization: float) -> str:
    if utilization < 50:
        return "#2ecc71"  # Green
    elif utilization < 75:
        return "#f39c12"  # Yellow/Orange
    elif utilization < 90:
        return "#e67e22"  # Dark Orange
    else:
        return "#e74c3c"  # Red


def format_countdown(resets_at: Optional[datetime]) -> str:
    if resets_at is None:
        return "N/A"
    now = datetime.now(timezone.utc)
    delta = resets_at - now
    total_seconds = int(delta.total_seconds())
    if total_seconds <= 0:
        return "리셋 중..."

    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days > 0:
        return f"{days}일 {hours}시간 후 리셋"
    elif hours > 0:
        return f"{hours}시간 {minutes}분 후 리셋"
    else:
        return f"{minutes}분 {seconds}초 후 리셋"

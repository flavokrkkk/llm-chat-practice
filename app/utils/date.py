from datetime import datetime, timedelta, timezone
from typing import Optional


def get_expires_at(base_time: Optional[datetime] = None, **kwargs) -> datetime:
    start = base_time or datetime.now(timezone.utc)

    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)

    return start + timedelta(**kwargs)

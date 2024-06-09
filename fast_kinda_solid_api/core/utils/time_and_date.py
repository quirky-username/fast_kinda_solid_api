from datetime import datetime

import pytz


def serialize_datetime(dt: datetime) -> str:
    if dt.tzinfo:
        return dt.astimezone(pytz.UTC).isoformat()
    else:
        return dt.replace(tzinfo=pytz.UTC).isoformat()


__all__ = [
    "serialize_datetime",
]

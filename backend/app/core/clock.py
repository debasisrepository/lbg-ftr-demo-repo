from datetime import datetime, timezone


class Clock:
    @staticmethod
    def utc_now() -> datetime:
        return datetime.now(timezone.utc)

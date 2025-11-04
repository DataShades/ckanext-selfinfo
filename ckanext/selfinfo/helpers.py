from __future__ import annotations

import datetime
import logging

log = logging.getLogger(__name__)


def selfinfo_is_profile_old(date_string: str, hours: int = 1) -> bool:
    try:
        date = datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S.%f")

        now = (
            datetime.datetime.utcnow()
        )  # Or datetime.now() if you're not using UTC
        ago = now - datetime.timedelta(hours=hours)
        if date < ago:
            return True
    except (ValueError, TypeError):
        log.error("Cannot compare Profile provided date.")

    return False

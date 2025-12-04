from __future__ import annotations

import datetime
import logging

from ckanext.selfinfo import config

log = logging.getLogger(__name__)


def selfinfo_action_name(action_name: str) -> str:
    """
    Construct action name with configured prefix.

    This helper ensures that action calls in templates and code use the
    correct prefixed action name based on the ckan.selfinfo.actions_prefix
    configuration.

    Args:
        action_name: The base action name without prefix

    Returns:
        The action name with prefix applied (e.g., "custom_selfinfo_get_ram"
        if prefix is "custom" and action_name is "selfinfo_get_ram")
    """
    prefix = config.selfinfo_get_actions_prefix()
    return f"{prefix}{action_name}"


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

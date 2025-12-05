from __future__ import annotations

from typing import Any

from . import action
from ckanext.selfinfo import config


def get_actions():
    prefix = config.selfinfo_get_actions_prefix()

    actions: dict[str, Any] = {
        f"{prefix}selftracking_store_tracks": action.selftracking_store_tracks,
        f"{prefix}selftracking_send_track_for_queue": action.selftracking_send_track_for_queue,
    }

    return actions

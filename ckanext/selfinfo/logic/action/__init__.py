from __future__ import annotations

from typing import Any

from . import get
from . import update
from . import delete
from ckanext.selfinfo import config


def get_actions():
    prefix = config.selfinfo_get_actions_prefix()

    actions: dict[str, Any] = {
        config.selfinfo_get_main_action_name(): get.get_selfinfo,
        f"{prefix}update_last_module_check": update.update_last_module_check,
        f"{prefix}selfinfo_get_ram": get.selfinfo_get_ram,
        f"{prefix}selfinfo_delete_profile": delete.selfinfo_delete_profile,
        "status_show": get.status_show,
    }

    return actions

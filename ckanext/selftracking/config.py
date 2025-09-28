from __future__ import annotations

from typing import Any

import ckan.plugins.toolkit as tk


SELFTRACKING_REDIS_PREFIX = "ckan.selftracking.redis_prefix"
SELFTRACKING_CATEGORIES = "ckan.selftracking.categories"
SELFTRACKING_REDIS_BATCH_SIZE = "ckan.selftracking.redis_batch_size"
SELFTRACKING_TRACK_TYPE_COLOR_PREFIX = "ckan.selftracking.type_color."


def selftracking_get_redis_prefix():
    return tk.config.get(SELFTRACKING_REDIS_PREFIX)


def selftracking_get_categories_list():
    return tk.config.get(SELFTRACKING_CATEGORIES)


def selftracking_redis_batch_size():
    return tk.config.get(SELFTRACKING_REDIS_BATCH_SIZE)


def selftracking_type_colors() -> dict[str, dict[str, Any]]:
    colors = {}
    prefix_len = len(SELFTRACKING_TRACK_TYPE_COLOR_PREFIX)
    options = {
        k: v
        for k, v in tk.config.items()
        if k.startswith(SELFTRACKING_TRACK_TYPE_COLOR_PREFIX)
    }
    for k, v in options.items():
        try:
            type = k[prefix_len:]
            colors[type.replace("_", " ")] = v
        except ValueError:
            continue

    return colors


def selftracking_type_color(type: str) -> str:
    color = tk.config.get(
        SELFTRACKING_TRACK_TYPE_COLOR_PREFIX + type.replace(" ", "_"), ""
    )
    return color

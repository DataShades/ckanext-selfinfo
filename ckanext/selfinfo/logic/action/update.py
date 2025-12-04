from __future__ import annotations

from typing import Any, Mapping
from datetime import datetime

try:
    from importlib.metadata import version as m_version
except ImportError:  # For Python<3.8
    from importlib_metadata import version as m_version
from ckan import types
from ckan.lib.redis import connect_to_redis, Redis
import ckan.plugins.toolkit as tk

from ckanext.selfinfo import utils, config


def update_last_module_check(
    context: types.Context,
    data_dict: dict[str, Any],
) -> dict[str, Any]:
    module = data_dict.get("module", "")

    tk.check_access("sysadmin", context, data_dict)

    if module:
        redis: Redis = connect_to_redis()

        redis_key: str = module + config.SELFINFO_REDIS_SUFFIX
        now: float = datetime.utcnow().timestamp()

        data: Mapping[str, Any] = {
            "name": module,
            "current_version": m_version(module),
            "updated": now,
            "latest_version": utils.get_lib_latest_version(module),
        }

        for key in data:
            if data[key] != redis.hget(redis_key, key):
                redis.hset(redis_key, key=key, value=data[key])

        raw_result = redis.hgetall(redis_key)
        result: dict[str, Any] = {
            k.decode("utf-8"): v.decode("utf-8")
            for k, v in raw_result.items()  # type: ignore
        }

        # Convert the updated timestamp to a human-readable format
        result["updated"] = str(
            datetime.fromtimestamp(float(result["updated"]))
        )

        return result
    return {}

from __future__ import annotations

import json
import logging
from typing import Any
from datetime import datetime, timezone

import ckan.plugins as p
from ckan.lib.redis import connect_to_redis, Redis

from ckanext.selftracking import interfaces
import ckanext.selftracking.config as s_config
from ckanext.selftracking.model.selftracking import SelfTrackingModel


SELFTRACKING_DEFAULT_CATEGORIES = [
    {
        "key": "main",
        "label": "Main",
        "snippet": "/selftracking/snippets/selftracking_main.html",
    },
    {
        "key": "page_view",
        "label": "Page View",
        "snippet": "/selftracking/snippets/selftracking_page_view.html",
    },
    {
        "key": "api_view",
        "label": "API View",
        "snippet": "/selftracking/snippets/selftracking_api_view.html",
    },
]
log = logging.getLogger(__name__)


def selftracking_add_track_to_redis(data_dict: dict[str, Any]) -> None:
    redis: Redis = connect_to_redis()

    try:
        key = s_config.selftracking_get_redis_prefix() + "_selftracking_tracks"
        redis.rpush(key, json.dumps(data_dict))
    except (ValueError, TypeError):
        log.error("Cannot store track in Redis.")

    return


def selftracking_store_tracks_in_db():
    batch_size = s_config.selftracking_redis_batch_size()
    redis: Redis = connect_to_redis()
    pipe = redis.pipeline()
    key = s_config.selftracking_get_redis_prefix() + "_selftracking_tracks"
    pipe.lrange(key, 0, batch_size - 1)
    pipe.ltrim(key, batch_size, -1)
    batch, _ = pipe.execute()
    for b in batch:
        # For testing big amount
        # for i in range(0, 100000):
        try:
            data = json.loads(b)
            try:
                track_time = data.get("track_time")
                if track_time:
                    track_time = datetime.fromtimestamp(
                        data["track_time"], tz=timezone.utc
                    )
                    data["track_time"] = track_time
            except Exception:
                pass
            SelfTrackingModel.create(data)
        except TypeError:
            log.error("Couldn't write track item to DB.")


def get_categories_list() -> list[dict[str, Any]]:
    categories = SELFTRACKING_DEFAULT_CATEGORIES

    # categories modification
    for item in p.PluginImplementations(interfaces.ISelftracking):
        item.selftracking_categories(categories)

    return categories


def get_selftracking_categories() -> list[dict[str, Any]]:
    categories = s_config.selftracking_get_categories_list()

    categories_list = [
        category for category in get_categories_list() if category["key"] in categories
    ]

    return categories_list

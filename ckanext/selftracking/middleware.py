from __future__ import annotations

from datetime import datetime

import ckan.plugins.toolkit as tk
import ckan.types as types

from ckanext.selftracking.utils import selftracking_add_track_to_redis


def track_activity(response: types.Response) -> types.Response:
    """Add activity to Redis list.

    Adds activity information to Redis list,
    which will be then added to DB.
    """
    path = tk.request.path
    if response.content_type == "text/html; charset=utf-8":
        ignore_paths = [
            "/api/i18n",
            "/favicon.ico",
        ]
        ignore_extensions = [".js", ".css"]

        if not [p for p in ignore_paths if p in path] and not [
            p for p in ignore_extensions if path.endswith(p)
        ]:
            user = tk.current_user
            data = {
                "path": path,
                "user": user.id if user.is_authenticated else "anonymous",
                "type": "page view",
                "track_time": datetime.utcnow().timestamp(),
            }

            selftracking_add_track_to_redis(data)

    elif response.content_type == "application/json;charset=utf-8" and path.startswith(
        "/api/action/"
    ):
        user = tk.current_user
        data = {
            "path": path,
            "user": user.id if user.is_authenticated else "anonymous",
            "type": "api view",
            "track_time": datetime.utcnow().timestamp(),
        }
        selftracking_add_track_to_redis(data)

    return response

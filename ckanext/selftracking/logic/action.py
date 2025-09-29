from __future__ import annotations

from datetime import datetime
import logging

import ckan.plugins.toolkit as tk
import ckan.types as types

import ckanext.selftracking.utils as s_utils


log = logging.getLogger(__name__)


def selftracking_store_tracks(context: types.Context, data_dict: types.DataDict):
    tk.check_access("selftracking_store_tracks", context, data_dict)

    s_utils.selftracking_store_tracks_in_db()

    return


def selftracking_send_track_for_queue(
    context: types.Context, data_dict: types.DataDict
):
    tk.check_access("selftracking_send_track_for_queue", context, data_dict)

    user = tk.current_user
    data = {
        "path": data_dict.get("path", ""),
        "user": user.id if user.is_authenticated else "anonymous",
        "type": data_dict.get("type", "missing type"),
        "track_time": datetime.utcnow().timestamp(),
    }

    s_utils.selftracking_add_track_to_redis(data)

    return

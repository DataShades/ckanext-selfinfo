from __future__ import annotations

from ckan.types import AuthResult, Context, DataDict


def selftracking_store_tracks(context: Context, data_dict: DataDict) -> AuthResult:
    return {"success": False}


def selftracking_send_track_for_queue(
    context: Context, data_dict: DataDict
) -> AuthResult:
    return {"success": True}

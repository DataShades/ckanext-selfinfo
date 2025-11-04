from __future__ import annotations

from typing import Any
from datetime import datetime, timedelta

from ckanext.selftracking.model.selftracking import SelfTrackingModel
import ckanext.selftracking.utils as tracking_utils


def selftracking_categories():
    return tracking_utils.get_selftracking_categories()


def selftracking_get_data() -> dict[str, Any]:
    count_by_type = SelfTrackingModel.get_tracks_by_types()
    tracks_last_24_hours = SelfTrackingModel.get_tracks_for_last_24_hours()
    track_types_count = SelfTrackingModel.get_tracks_count_for_x_days(30)

    return {
        "count_by_type": count_by_type,
        "tracks_last_24_hours": tracks_last_24_hours,
        "track_types_count": track_types_count,
    }


def selftracking_get_view_data(
    type: str,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> list[Any]:
    options = {
        "from_date": from_date,
        "to_date": to_date,
    }
    view_data = SelfTrackingModel.get_tracks_per_type(type, options)
    return view_data


def selftracking_get_date(minus_days: int = 0):
    date = datetime.utcnow()

    if minus_days:
        date = date - timedelta(days=minus_days)

    return date

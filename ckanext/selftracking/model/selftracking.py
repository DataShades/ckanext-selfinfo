from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from typing import Any, List
import hashlib

import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.selftracking.config as tracking_config


class SelfTrackingModel(tk.BaseModel):  # type: ignore
    __tablename__ = "selftracking"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    path = sa.Column(sa.Text, nullable=False)
    user = sa.Column(sa.String, nullable=False)
    type = sa.Column(sa.String, nullable=False)
    track_time = sa.Column(sa.DateTime, default=datetime.utcnow)
    extras = sa.Column(MutableDict.as_mutable(JSONB))

    @classmethod
    def get_by_id(cls: type[SelfTrackingModel], id: str) -> SelfTrackingModel | None:
        return model.Session.query(cls).filter(cls.id == id).first()

    @classmethod
    def get_by_path(
        cls: type[SelfTrackingModel], alias: str
    ) -> SelfTrackingModel | None:
        return model.Session.query(cls).filter(cls.alias == alias).first()

    @classmethod
    def get_by_type(cls: type[SelfTrackingModel], type: str) -> list[SelfTrackingModel]:
        return (
            model.Session.query(cls)
            .filter(cls.type == type)
            .order_by(cls.track_time.desc())
            .all()
        )

    @classmethod
    def get_all(cls: type[SelfTrackingModel]) -> list[SelfTrackingModel]:
        return model.Session.query(cls).order_by(cls.track_time.desc()).all()

    @classmethod
    def create(
        cls: type[SelfTrackingModel], data_dict: dict[str, Any]
    ) -> SelfTrackingModel:
        selftrack = cls(**data_dict)

        model.Session.add(selftrack)
        model.Session.commit()

        return selftrack

    def delete(self) -> None:
        model.Session().autoflush = False
        model.Session.delete(self)
        model.Session.commit()

    def update(self, data_dict: dict[str, Any]) -> None:
        for key, value in data_dict.items():
            setattr(self, key, value)
        model.Session.commit()

    @classmethod
    def color_from_type(cls: type[SelfTrackingModel], type_: str) -> str:
        color = tracking_config.selftracking_type_color(type_)

        if not color:
            h = hashlib.md5(type_.encode()).hexdigest()
            return "#" + h[-6:]

        return color

    @classmethod
    def get_tracks_by_types(cls: type[SelfTrackingModel]) -> list[dict[str, Any]]:
        results = (
            model.Session.query(cls.type, sa.func.count(cls.id))
            .group_by(cls.type)
            .all()
        )

        results = [
            {"type": t[0], "count": t[1], "color": cls.color_from_type(t[0])}
            for t in results
        ]

        return results

    @classmethod
    def get_tracks_by_type_and_days(
        cls: type[SelfTrackingModel], type: str, days: int
    ) -> dict[str, Any]:
        since = datetime.utcnow() - timedelta(days=days)
        results = (
            model.Session.query(
                sa.func.date_trunc("day", cls.track_time).label("day"),
                sa.func.count().label("count"),
            )
            .filter(cls.type == type)
            .filter(cls.track_time >= since)
            .group_by(sa.func.date_trunc("day", cls.track_time))
            .order_by("day")
            .all()
        )

        labels = [r.day.strftime("%Y-%m-%d") for r in results]
        values = [r.count for r in results]

        data = {"labels": labels, "values": values}

        return {"raw": data, "json": json.dumps(data)}

    @classmethod
    def get_tracks_count_for_x_days(
        cls: type[SelfTrackingModel], days: int
    ) -> dict[Any, Any]:
        since = datetime.utcnow() - timedelta(days=days)
        results = (
            model.Session.query(
                cls.type,
                sa.func.date_trunc("day", cls.track_time).label("day"),
                sa.func.count().label("count"),
            )
            .filter(cls.track_time >= since)
            .group_by(cls.type, sa.func.date_trunc("day", cls.track_time))
            .order_by(cls.type, "day")
            .all()
        )

        data = {}
        for r in results:
            type_ = r.type
            if type_ not in data:
                data[type_] = {
                    "labels": [],
                    "values": [],
                    "color": cls.color_from_type(type_),
                }
            data[type_]["labels"].append(r.day.strftime("%Y-%m-%d"))
            data[type_]["values"].append(r.count)

        return data

    @classmethod
    def get_tracks_per_type(
        cls: type[SelfTrackingModel], type: str, t_days: int | None = None
    ) -> List[Any]:

        q = model.Session.query(cls.path, sa.func.count().label("count")).filter(
            cls.type == type
        )

        if t_days:
            since = datetime.utcnow() - timedelta(days=t_days)
            q = q.filter(cls.track_time >= since)

        q = q.group_by(cls.path).order_by(sa.func.count().desc()).all()

        return q

    @classmethod
    def get_tracks_for_last_24_hours(cls: type[SelfTrackingModel]) -> dict[str, Any]:
        end_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        start_time = end_time - timedelta(hours=23)
        results = (
            model.Session.query(
                cls.type,
                sa.func.date_trunc("hour", cls.track_time).label("hour"),
                sa.func.count().label("count"),
            )
            .filter(cls.track_time >= start_time, cls.track_time <= end_time)
            .group_by(cls.type, "hour")
            .order_by(cls.type, "hour")
            .all()
        )

        data = {key: {} for key, _, _ in results}
        for event_type, hour, count in results:
            local_hour = hour.replace(tzinfo=timezone.utc).astimezone()
            data[event_type][local_hour.strftime("%H:%M")] = count

        labels = [
            (start_time + timedelta(hours=i)).astimezone().strftime("%H:%M")
            for i in range(24)
        ]

        items = {}
        for event_type in data.keys():
            items[event_type] = {
                "label": event_type,
                "data": [data[event_type].get(hour, 0) for hour in labels],
                "color": cls.color_from_type(event_type),
            }

        result = {
            "items": items,
            "labels": labels,
        }
        return result

from __future__ import annotations

from flask import Blueprint
from typing import cast, Any
from datetime import datetime

import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as dict_fns
from ckan import types
import ckan.model as model
from ckan.common import _, request
import ckan.logic as logic

from ckanext.selftracking.model.selftracking import SelfTrackingModel

selftracking = Blueprint("selftracking", __name__)


@selftracking.route("/ckan-admin/selftracking/index")
def index() -> Any | str:
    try:
        context: types.Context = cast(
            types.Context,
            {
                "model": model,
                "user": tk.current_user.name,
                "auth_user_obj": tk.current_user,
            },
        )

        tk.check_access("sysadmin", context)
    except tk.NotAuthorized:
        tk.abort(404)

    return tk.render(
        "selftracking/index.html",
        extra_vars={},
    )


@selftracking.route("/ckan-admin/selftracking/path/data")
def selftracking_path_data() -> Any | str:
    try:
        context: types.Context = cast(
            types.Context,
            {
                "model": model,
                "user": tk.current_user.name,
                "auth_user_obj": tk.current_user,
            },
        )

        tk.check_access("sysadmin", context)
    except tk.NotAuthorized:
        tk.abort(404)

    extra_vars = {}

    path = request.args.get("path", "")

    results = SelfTrackingModel.get_by_path(path)

    extra_vars["path_view_data"] = results
    extra_vars["path"] = path

    return tk.render(
        "selftracking/results/selftracking_path_view_results.html",
        extra_vars,
    )


@selftracking.route("/ckan-admin/selftracking/view/query", methods=["POST"])
def selftracking_views_query() -> Any | str:
    context: types.Context = cast(
        types.Context,
        {
            "model": model,
            "user": tk.current_user.name,
            "auth_user_obj": tk.current_user,
        },
    )
    try:
        tk.check_access("sysadmin", context)
    except tk.NotAuthorized:
        tk.abort(404)

    try:
        data_dict = logic.clean_dict(
            dict_fns.unflatten(
                logic.tuplize_dict(logic.parse_params(request.form))
            )
        )
    except dict_fns.DataError:
        return tk.base.abort(400, _("Integrity Error"))

    from_date = None
    to_date = None
    username = data_dict.get("username")
    view_type = data_dict.get("type", "")
    if data_dict.get("from_date"):
        try:
            from_date = datetime.strptime(
                data_dict.get("from_date", ""), "%Y-%m-%d"
            )
        except ValueError:
            pass

    if data_dict.get("to_date"):
        try:
            to_date = datetime.strptime(
                data_dict.get("to_date", ""), "%Y-%m-%d"
            )
        except ValueError:
            pass

    options = {
        "from_date": from_date,
        "to_date": to_date,
        "username": username,
    }

    view_data = SelfTrackingModel.get_tracks_per_type(view_type, options)

    return tk.render(
        "/selftracking/results/selftracking_type_views_table.html",
        extra_vars={
            "data": view_data,
            "type": view_type,
            "type_machine": view_type.replace(" ", "-"),
        },
    )

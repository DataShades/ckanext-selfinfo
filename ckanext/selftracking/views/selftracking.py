from __future__ import annotations

from flask import Blueprint
from typing import cast

import ckan.plugins.toolkit as tk
from ckan import types
import ckan.model as model
from ckan.common import _, request

from ckanext.selftracking.model.selftracking import SelfTrackingModel

selftracking = Blueprint("selftracking", __name__)


@selftracking.route("/ckan-admin/selftracking/index")
def index():
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
def selftracking_path_data():
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

from __future__ import annotations

import json
from typing import cast, Any
from flask import Blueprint, Response
from urllib.parse import urlencode
from cryptography.fernet import Fernet, InvalidToken
import gzip
from werkzeug.utils import secure_filename

from ckan import types
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.common import _, request

import ckanext.selftools.config as selftools_config


selftools_htmx = Blueprint("selftools_htmx", __name__)


@selftools_htmx.route("/selftools/solr-query", methods=["POST"])
def selftools_solr_query() -> Any | str:
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
            dict_fns.unflatten(logic.tuplize_dict(logic.parse_params(request.form)))
        )
    except dict_fns.DataError:
        return tk.base.abort(400, _("Integrity Error"))

    resp = tk.get_action("selftools_solr_query")(context, data_dict)

    pretty_json = json.dumps(resp, indent=2)

    return tk.render(
        "/selftools/results/pretty_json.html", extra_vars={"json": pretty_json}
    )


@selftools_htmx.route("/selftools/solr-delete", methods=["POST"])
def selftools_solr_delete() -> Any | str:
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
            dict_fns.unflatten(logic.tuplize_dict(logic.parse_params(request.form)))
        )
    except dict_fns.DataError:
        return tk.base.abort(400, _("Integrity Error"))

    resp = tk.get_action("selftools_solr_delete")(context, data_dict)

    if not resp.get("success"):
        return resp["message"] if resp.get("message") else _("Couldn't delete index.")
    else:
        return _("Deleted.")


@selftools_htmx.route("/selftools/solr-index", methods=["POST"])
def selftools_solr_index() -> Any | str:
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
            dict_fns.unflatten(logic.tuplize_dict(logic.parse_params(request.form)))
        )
    except dict_fns.DataError:
        return tk.base.abort(400, _("Integrity Error"))

    resp = tk.get_action("selftools_solr_index")(context, data_dict)

    if not resp.get("success"):
        return (
            resp["message"]
            if resp.get("message")
            else _("Couldn't index dataset. No such Dataset.")
        )
    else:
        return _("Indexed.")


@selftools_htmx.route("/selftools/db-query", methods=["POST"])
def selftools_db_query() -> Any | str:
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
            dict_fns.unflatten(logic.tuplize_dict(logic.parse_params(request.form)))
        )
    except dict_fns.DataError:
        return tk.base.abort(400, _("Integrity Error"))

    resp = tk.get_action("selftools_db_query")(context, data_dict)

    if not resp.get("success"):
        return resp["message"] if resp.get("message") else _("Something went wrong...")
    else:
        return tk.render(
            "/selftools/results/db_results.html", extra_vars={"data": resp}
        )


@selftools_htmx.route("/selftools/db-update", methods=["POST"])
def selftools_db_update() -> Any | str:
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
            dict_fns.unflatten(logic.tuplize_dict(logic.parse_params(request.form)))
        )
    except dict_fns.DataError:
        return tk.base.abort(400, _("Integrity Error"))

    resp = tk.get_action("selftools_db_update")(context, data_dict)

    if not resp.get("success"):
        return resp["message"] if resp.get("message") else _("Something went wrong...")
    else:
        return tk.render(
            "/selftools/results/db_effected.html", extra_vars={"data": resp}
        )


@selftools_htmx.route("/selftools/redis-query", methods=["POST"])
def selftools_redis_query() -> Any | str:
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
            dict_fns.unflatten(logic.tuplize_dict(logic.parse_params(request.form)))
        )
    except dict_fns.DataError:
        return tk.base.abort(400, _("Integrity Error"))

    resp = tk.get_action("selftools_redis_query")(context, data_dict)

    if not resp.get("success"):
        return resp["message"] if resp.get("message") else _("Something went wrong...")
    else:
        return tk.render(
            "/selftools/results/redis_results.html", extra_vars={"data": resp}
        )


@selftools_htmx.route("/selftools/redis-update", methods=["POST"])
def selftools_redis_update() -> Any | str:
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
            dict_fns.unflatten(logic.tuplize_dict(logic.parse_params(request.form)))
        )
    except dict_fns.DataError:
        return tk.base.abort(400, _("Integrity Error"))

    resp = tk.get_action("selftools_redis_update")(context, data_dict)

    if not resp.get("success"):
        return resp["message"] if resp.get("message") else _("Something went wrong...")
    else:
        return _("Updated/Created.")


@selftools_htmx.route("/selftools/redis-delete", methods=["POST"])
def selftools_redis_delete() -> Any | str:
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
            dict_fns.unflatten(logic.tuplize_dict(logic.parse_params(request.form)))
        )
    except dict_fns.DataError:
        return tk.base.abort(400, _("Integrity Error"))

    resp = tk.get_action("selftools_redis_delete")(context, data_dict)

    if not resp.get("success"):
        return (
            resp["message"]
            if resp.get("message")
            else _("Couldn't delete Key. No such Key.")
        )
    else:
        return _("Deleted.")


@selftools_htmx.route("/selftools/config-query", methods=["POST"])
def selftools_config_query() -> Any | str:
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
            dict_fns.unflatten(logic.tuplize_dict(logic.parse_params(request.form)))
        )
    except dict_fns.DataError:
        return tk.base.abort(400, _("Integrity Error"))

    resp = tk.get_action("selftools_config_query")(context, data_dict)

    if not resp.get("success"):
        return resp["message"] if resp.get("message") else _("Something went wrong...")
    else:
        return tk.render(
            "/selftools/results/config_results.html", extra_vars={"data": resp}
        )


@selftools_htmx.route("/selftools/model-export", methods=["POST"])
def selftools_model_export() -> Any | str:
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
            dict_fns.unflatten(logic.tuplize_dict(logic.parse_params(request.form)))
        )
    except dict_fns.DataError:
        return tk.base.abort(400, _("Integrity Error"))

    resp = tk.get_action("selftools_model_export")(context, data_dict)

    if not resp.get("success"):
        return resp["message"] if resp.get("message") else _("Something went wrong...")
    else:
        r_length = len(resp["results"])
        show_100 = dict(list(resp["results"].items())[:100])
        pretty_json = json.dumps(show_100, indent=2)

        query_string = urlencode(data_dict, doseq=True)
        download_link = "?".join(
            [
                tk.h.url_for(
                    "selftools_htmx.selftools_model_export_download", _external=True
                ),
                query_string,
            ]
        )

        return tk.render(
            "/selftools/results/model_results.html",
            extra_vars={
                "json": pretty_json,
                "download_link": download_link,
                "r_length": r_length,
            },
        )


@selftools_htmx.route("/selftools/model-export-download", methods=["GET"])
def selftools_model_export_download() -> Any | str:
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
        data_dict = {k: v if len(v) > 1 else v[0] for k, v in request.args.lists()}

    except dict_fns.DataError:
        return tk.base.abort(400, _("Integrity Error"))

    resp = tk.get_action("selftools_model_export")(context, data_dict)

    if not resp.get("success"):
        return resp["message"] if resp.get("message") else _("Something went wrong...")
    else:
        json_bytes = json.dumps(resp["results"]).encode("utf-8")
        compressed = gzip.compress(json_bytes)
        key = selftools_config.selftools_get_model_ecryption_key()

        if key:
            fernet = Fernet(key)
            encrypted = fernet.encrypt(compressed)

            response = Response(encrypted, mimetype="application/octet-stream")
            response.headers["Content-Disposition"] = (
                "attachment; filename=model_export.bin"
            )
        else:
            response = Response(compressed, mimetype="application/gzip")
            response.headers["Content-Disposition"] = (
                "attachment; filename=model_export.gz"
            )

        return response


@selftools_htmx.route(
    "/selftools/model-export-custom-relationships-fields", methods=["POST"]
)
def selftools_model_export_custom_relationships_fields() -> Any | str:
    return tk.render(
        "/selftools/tools/model/model_export_custom_relationships_fields.html",
        extra_vars={},
    )


@selftools_htmx.route(
    "/selftools/model-export-default-value-condition", methods=["POST"]
)
def selftools_model_export_custom_default_value_condition() -> Any | str:
    return tk.render(
        "/selftools/tools/model/model_export_custom_default_value_condition.html",
        extra_vars={},
    )


@selftools_htmx.route("/selftools/model-import", methods=["POST"])
def selftools_model_import() -> Any | str:
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

    file = request.files.get("file")

    try:
        data_dict = logic.clean_dict(
            dict_fns.unflatten(logic.tuplize_dict(logic.parse_params(request.form)))
        )
    except dict_fns.DataError:
        return tk.base.abort(400, _("Integrity Error"))

    if not file:
        return "No file provided"

    filename = file.filename if file.filename else ""
    try:
        sfilename = secure_filename(filename)
        f_extension = sfilename.split(".")[-1]
        data = file.read()

        key = (
            data_dict["decryption_key"]
            if data_dict.get("decryption_key")
            else selftools_config.selftools_get_model_ecryption_key()
        )

        if f_extension == "bin" and key:
            fernet = Fernet(key)
            decrypted = fernet.decrypt(data)
            decompressed = gzip.decompress(decrypted).decode("utf-8")
        else:
            decompressed = gzip.decompress(data).decode("utf-8")

        data_dict["models_data"] = json.loads(decompressed)

        resp = tk.get_action("selftools_model_import")(context, data_dict)

        if not resp.get("success"):
            return (
                resp["message"] if resp.get("message") else _("Something went wrong...")
            )
        else:
            return _("Finished.")
    except InvalidToken:
        return _("Cannot decrypt the file.")
    except Exception as e:
        return str(e)

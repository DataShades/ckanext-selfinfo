from __future__ import annotations

import requests
import logging
import json
from sqlalchemy import desc, exc as sql_exceptions
from sqlalchemy.inspection import inspect
import redis
from typing import Any, Literal
from datetime import datetime

from ckan import types
import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.lib.search.common import (
    is_available as solr_available,
    make_connection as solr_connection,
)
from ckan.lib.search import clear, rebuild, commit
from ckan.lib.redis import connect_to_redis, Redis

from ckanext.selftools import utils, config

log = logging.getLogger(__name__)


def selftools_solr_query(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any] | Literal[False]:
    tk.check_access("sysadmin", context, data_dict)

    if solr_available():
        solr = solr_connection()
        solr_url = solr.url
        max_limit = config.selftools_get_operations_limit()
        default_search = "q=*:*&rows=" + str(max_limit)

        search = data_dict.get("q", default_search)

        if "rows=" not in search:
            search += "&rows=" + str(max_limit)
        q_response = requests.get(solr_url.rstrip("/") + "/query?" + search)
        q_response.raise_for_status()

        query = q_response.json()

        return query
    return False


def selftools_solr_delete(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any]:
    tk.check_access("sysadmin", context, data_dict)

    if not utils.selftools_verify_operations_pwd(data_dict.get("selftools_pwd")):
        return {"success": False, "message": "Unauthorized action."}

    # Really need to check? It can be not only Datasets
    # pkg = model.Package.get(data_dict.get("id"))
    # if not pkg:
    #     return {"success": False}

    clear(data_dict.get("id", ""))
    return {"success": True}


def selftools_solr_index(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any]:
    tk.check_access("sysadmin", context, data_dict)
    id = data_dict.get("id")
    ids = data_dict.get("ids")

    if not id and not ids:
        return {
            "success": False,
            "message": "Dataset ID or multiple IDs should be provided.",
        }
    pkg = None
    if id:
        pkg = model.Package.get(id)

    try:
        rebuild(
            package_id=pkg.id if pkg else None,
            force=tk.asbool(data_dict.get("force", "False")),
            package_ids=json.loads(ids) if ids else [],
        )
        commit()
    except Exception:
        return {"success": False, "message": "An Error appeared while indexing."}
    return {"success": True}


def selftools_db_query(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any] | Literal[False]:
    tk.check_access("sysadmin", context, data_dict)

    q_model = data_dict.get("model")
    limit = data_dict.get("limit")
    field = data_dict.get("field")
    value = data_dict.get("value")
    order = data_dict.get("order")
    order_by = data_dict.get("order_by")
    if q_model:
        model_fields_blacklist = [
            b.strip().split(".") for b in config.selftools_get_model_fields_blacklist()
        ]
        combained_blacklist = [
            *model_fields_blacklist,
            *[["User", "password"], ["User", "apikey"]],
        ]

        def _get_db_row_values(row: Any, columns: Any, model_name: str) -> list[Any]:
            values = []
            for col in columns:
                if [
                    b for b in combained_blacklist if b[0] == model_name and col == b[1]
                ]:
                    value = "SECURE"
                else:
                    value = getattr(row, col, None)

                if value is not None:
                    values.append(value)
                else:
                    values.append("")

            return values

        models = utils.get_db_models()
        curr_model = [m for m in models if m["label"] == q_model]

        if curr_model:
            try:
                model_class = curr_model[0]["model"]
                q = model.Session.query(model_class)

                if field and value:
                    q = q.filter(getattr(model_class, field) == value)

                if order_by and order:
                    if order == "desc":
                        q = q.order_by(desc(order_by))
                    else:
                        q = q.order_by(order_by)

                if limit:
                    q = q.limit(int(limit))

                results = q.all()

                columns = [col.name for col in inspect(model_class).c]

                structured_results = [
                    _get_db_row_values(row, columns, curr_model[0]["label"])
                    for row in results
                ]

                return {
                    "success": True,
                    "results": structured_results,
                    "fields": columns,
                }
            except (AttributeError, sql_exceptions.CompileError) as e:
                return {
                    "success": False,
                    "message": str(e),
                }
    return False


def selftools_db_update(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any]:
    tk.check_access("sysadmin", context, data_dict)

    if not utils.selftools_verify_operations_pwd(data_dict.get("selftools_pwd")):
        return {"success": False, "message": "Unauthorized action."}

    q_model = data_dict.get("model")
    limit = data_dict.get("limit")
    field = data_dict.get("field")
    value = data_dict.get("value")
    where_field = data_dict.get("where_field")
    where_value = data_dict.get("where_value")
    if q_model:
        models = utils.get_db_models()
        curr_model = [m for m in models if m["label"] == q_model]

        if curr_model:
            try:
                model_class = curr_model[0]["model"]
                table_details = inspect(model_class)

                primary_key = None
                try:
                    primary_name = table_details.primary_key[0].name
                    primary_key = getattr(model_class, primary_name)
                except Exception:
                    return {
                        "success": False,
                        "message": "Cannot extract Primary key for the Model.",
                    }

                # First filter and limit results
                q = model.Session.query(primary_key)

                if where_field and where_value:
                    q = q.filter(getattr(model_class, where_field) == where_value)

                if limit:
                    q = q.limit(int(limit))

                if field and value:
                    ids = [i[0] for i in q.all()]
                    # Update already limited results
                    upd = (
                        model.Session.query(model_class)
                        .filter(primary_key.in_(ids))
                        .update({field: value})
                    )

                    model.Session.commit()

                    return {
                        "success": True,
                        "updated": upd,
                        "effected": ids,
                        "effected_json": json.dumps(ids, indent=2),
                    }
                else:
                    return {"success": False, "message": "Provide the WHERE condition"}
            except AttributeError:
                return {
                    "success": False,
                    "message": f"There no attribute '{field}' in '{curr_model[0]['label']}'",
                }

    return {"success": False}


def selftools_redis_query(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any] | Literal[False]:
    tk.check_access("sysadmin", context, data_dict)

    def _redis_key_value(redis_conn: Any, key: str):
        key_type = redis_conn.type(key).decode("utf-8")
        val = ""
        try:
            if key_type == "string":
                val = redis_conn.get(key)
            elif key_type == "hash":
                val = redis_conn.hgetall(key)
            elif key_type == "list":
                length = redis_conn.llen(key)
                val = str(
                    [item.decode("utf-8") for item in redis_conn.lrange(key, 0, 24)]
                )
                if length > 25:
                    val += f" showing only first 25 elements, current number of elements is {length}"
            else:
                val = f"<Unsupported type: {key_type}>"
        except redis.exceptions.RedisError as e:  # pyright: ignore
            val = f"<Error: {str(e)}>"

        return val

    def _safe_key_display(k: bytes) -> str:
        try:
            # Check for binary prefix or signs of pickled data
            if any(s in repr(k) for s in [r"\x80", r"\x00"]):
                return repr(k)
            return k.decode("utf-8")
        except UnicodeDecodeError:
            return repr(k)

    redis_conn: Redis = connect_to_redis()

    q = data_dict.get("q", "")
    if q:
        keys = redis_conn.keys(f"*{q}*")
        max_limit = config.selftools_get_operations_limit()
        keys = keys[:max_limit]  # pyright: ignore
        redis_results = [
            {
                "key": _safe_key_display(k),
                "type": redis_conn.type(k).decode("utf-8"),  # pyright: ignore
                "value": str(_redis_key_value(redis_conn, k)),
            }
            for k in keys
        ]

        return {"success": True, "results": redis_results}
    return False


def selftools_redis_update(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any]:
    tk.check_access("sysadmin", context, data_dict)

    if not utils.selftools_verify_operations_pwd(data_dict.get("selftools_pwd")):
        return {"success": False, "message": "Unauthorized action."}

    key = data_dict.get("redis_key")
    value = data_dict.get("value")
    if key and value:
        redis_conn: Redis = connect_to_redis()
        redis_conn.set(key, value)
        return {"success": True}

    return {"success": False}


def selftools_redis_delete(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any]:
    tk.check_access("sysadmin", context, data_dict)

    if not utils.selftools_verify_operations_pwd(data_dict.get("selftools_pwd")):
        return {"success": False, "message": "Unauthorized action."}

    key = data_dict.get("redis_key")
    if key:
        redis_conn: Redis = connect_to_redis()

        deleted = redis_conn.delete(key)
        if deleted:
            return {"success": True}
    return {"success": False}


def selftools_config_query(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any]:
    tk.check_access("sysadmin", context, data_dict)

    if not utils.selftools_verify_operations_pwd(data_dict.get("selftools_pwd")):
        return {"success": False, "message": "Unauthorized action."}

    key = data_dict.get("q")
    if key:
        blacklist = config.selftools_get_config_blacklist()
        default_blacklist = [
            "sqlalchemy.url",
            "ckan.datastore.write_url",
            "ckan.datastore.read_url",
            "solr_url",
            "solr_user",
            "solr_password",
            "ckan.redis.url",
            config.SELFTOOLS_CONFIG_BLACKLIST,
            config.SELFTOOLS_OPERATIONS_PWD,
        ]
        config_keys = tk.config.keys()
        config_keys = [
            k for k in config_keys if k not in [*default_blacklist, *blacklist]
        ]
        config_results = [
            {"key": ck, "value": tk.config.get(ck)} for ck in config_keys if key in ck
        ]
        return {"success": True, "results": config_results}

    return {"success": False}


def selftools_model_export(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any] | Literal[False]:
    tk.check_access("sysadmin", context, data_dict)

    if not utils.selftools_verify_operations_pwd(data_dict.get("selftools_pwd")):
        return {"success": False, "message": "Unauthorized action."}

    q_model = data_dict.get("model")
    limit = data_dict.get("limit")
    locals = data_dict.get("local[]", [])
    remotes = data_dict.get("remote[]", [])
    custom_relationships = []

    if locals and remotes:
        for r in (
            list(zip(locals, remotes))
            if isinstance(locals, list)
            else [(locals, remotes)]
        ):
            local = r[0].split(".")
            remote = r[1].split(".")

            if not len(local) == 2 or not len(remote) == 2:
                return {
                    "success": False,
                    "message": "Issue with extracting Custom Relationships, please review them.",
                }
            custom_relationships.append(
                {
                    "local_model": local[0],
                    "local_field": local[1],
                    "remote_model": remote[0],
                    "remote_field": remote[1],
                }
            )

    # default value condition zip
    default_value_conditions_field = [
        "default_value_condition_model[]",
        "default_value_condition_field[]",
        "default_value_condition_value[]",
        "default_value_condition_set_field[]",
        "default_value_condition_set_value[]",
    ]
    columns = map(lambda key: data_dict.get(key, []), default_value_conditions_field)
    default_value_conditions = list(zip(*columns))

    if q_model:

        def _to_string(value: str):
            if isinstance(value, datetime):
                return value.isoformat()
            return value

        def _collect(
            row: dict[str, Any],
            model_class: Any,
            collector: dict[str, Any],
            default_models: Any,
        ) -> None | dict[str, Any]:
            model_name = model_class.__name__
            table_details = inspect(model_class)

            primary_name = None
            try:
                primary_name = table_details.primary_key[0].name
            except Exception:
                return {
                    "success": False,
                    "message": "Cannot extract Primary name for the Model.",
                }

            relationships = table_details.relationships
            columns = [col.name for col in table_details.c]

            values = {}
            primary_value = ""
            for col in columns:
                value = getattr(row, col, None)

                if value is not None:
                    values[col] = _to_string(value)
                else:
                    values[col] = None

                if col == primary_name:
                    primary_value = value

            unique_key = model_name + "." + primary_value

            if unique_key not in collector:
                collector[unique_key] = {
                    "model": model_name,
                    "primary_key": primary_name,
                    "values": values,
                }

                for _, rel in relationships.items():
                    class_field = None
                    local_key = None
                    for local_col, remote_col in rel.local_remote_pairs:
                        remote_key = remote_col.name
                        local_key = local_col.name

                        class_field = getattr(rel.mapper.class_, remote_key)
                    if class_field and local_key:
                        rows = (
                            model.Session.query(rel.mapper.class_)
                            .filter(class_field == values[local_key])
                            .all()
                        )
                        if rows:
                            [
                                _collect(
                                    row, rel.mapper.class_, collector, default_models
                                )
                                for row in rows
                            ]

            if c_r := [
                i for i in custom_relationships if i["local_model"] == model_name
            ]:
                for r in c_r:
                    r_m = [m for m in default_models if m["label"] == r["remote_model"]]
                    if r_m and r["local_field"] in values:
                        remote_model = r_m[0]["model"]
                        class_field = getattr(remote_model, r["remote_field"])

                        rows = (
                            model.Session.query(remote_model)
                            .filter(class_field == values[r["local_field"]])
                            .all()
                        )
                        if rows:
                            [
                                _collect(row, remote_model, collector, default_models)
                                for row in rows
                            ]

            if default_value_conditions:
                matches = [
                    condition
                    for condition in default_value_conditions
                    if model_name == condition[0]
                    and condition[1] in values
                    and condition[2] == values[condition[1]]
                ]

                if matches:
                    for m in matches:
                        collector[unique_key]["values"][m[3]] = m[4]

        default_models = utils.get_db_models()
        curr_model = [m for m in default_models if m["label"] == q_model]

        if curr_model:
            field = data_dict.get("field")
            value = data_dict.get("value")

            try:
                model_class = curr_model[0]["model"]
                q = model.Session.query(model_class)

                if field and value:
                    q = q.filter(getattr(model_class, field) == value)

                if limit:
                    q = q.limit(int(limit))

                results = q.all()
                collector = {}
                [
                    _collect(row, model_class, collector, default_models)
                    for row in results
                ]

                return {
                    "success": True,
                    "results": collector,
                }
            except (AttributeError, sql_exceptions.CompileError) as e:
                return {
                    "success": False,
                    "message": str(e),
                }
    return False


def selftools_model_import(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any] | Literal[False]:

    tk.check_access("sysadmin", context, data_dict)

    if not utils.selftools_verify_operations_pwd(data_dict.get("selftools_pwd")):
        return {"success": False, "message": "Unauthorized action."}

    default_models = utils.get_db_models()
    inserted_list = []
    models_data = data_dict.get("models_data", {})

    def _get_model_class(name: str):
        return [m for m in default_models if m["label"] == name][0]["model"]

    def _get_model_relations(model_names: Any) -> dict[str, Any]:
        """
        Returns:
        {
            'PackageExtra': {
                'Package': {
                    'local_column': 'package_id',
                    'remote_column': 'id'
                }
            },
            ...
        }
        """
        dependencies = {}

        for model_name in model_names:
            model_cls = _get_model_class(model_name)
            deps = {}

            for rel in inspect(model_cls).relationships:
                if not rel.direction.name.startswith("MANYTOONE"):
                    continue  # Only track dependencies, not backrefs

                related_cls = rel.mapper.class_
                related_model_name = related_cls.__name__

                if related_model_name in model_names:
                    # Should be a 1:1 mapping between local and remote columns
                    local_column = next(iter(rel.local_columns)).name
                    remote_column = next(iter(rel.remote_side)).name

                    deps[related_model_name] = {
                        "local_column": local_column,
                        "remote_column": remote_column,
                    }

            dependencies[model_name] = deps

        return dependencies

    def _try_to_datetime(value: Any):
        if value and isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                pass

        return value

    def _create_row(rid: str, row: dict[str, Any]):
        if rid in inserted_list:
            return

        model_name = row["model"]
        model_class = _get_model_class(model_name)
        values = row["values"]
        primary_name = row["primary_key"]

        if model_relations.get(model_name):
            # Insert firstly the parent related row
            for m, k in model_relations[model_name].items():
                local_value = values.get(k["local_column"])

                dict_key = ".".join([m, local_value])

                if models_data.get(dict_key):
                    _create_row(dict_key, models_data[dict_key])

        primary_key = getattr(model_class, primary_name)

        session = model.Session()

        obj_id = values.get(primary_name)
        r_obj = model.Session.query(model_class).filter(primary_key == obj_id).first()

        if not r_obj:
            r_obj = model_class()
        for k, v in values.items():
            setattr(r_obj, k, _try_to_datetime(v))

        try:
            session.add(r_obj)
            session.commit()
            inserted_list.append(rid)
        except sql_exceptions.IntegrityError:
            session.rollback()

    try:
        model_classes = {v["model"] for v in models_data.values()}
        model_relations = _get_model_relations(model_classes)

        for rid, row in models_data.items():
            _create_row(rid, row)
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
        }
    return {"success": True}

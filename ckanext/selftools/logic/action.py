from __future__ import annotations

import requests
import logging
import json
from sqlalchemy import desc, exc as sql_exceptions, text
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
from ckanext.selfinfo import config as selfinfo_config

# Import datastore backend functions for proper connection handling
try:
    from ckanext.datastore.backend.postgres import get_read_engine

    datastore_available = True
except ImportError:
    datastore_available = False
    get_read_engine = None

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

    if not utils.selftools_verify_operations_pwd(
        data_dict.get("selftools_pwd")
    ):
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
        return {
            "success": False,
            "message": "An Error appeared while indexing.",
        }
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
            b.strip().split(".")
            for b in config.selftools_get_model_fields_blacklist()
        ]
        combained_blacklist = [
            *model_fields_blacklist,
            *[["User", "password"], ["User", "apikey"]],
        ]

        def _get_db_row_values(
            row: Any, columns: Any, model_name: str
        ) -> list[Any]:
            values = []
            for col in columns:
                if [
                    b
                    for b in combained_blacklist
                    if b[0] == model_name and col == b[1]
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
            except (
                AttributeError,
                sql_exceptions.CompileError,
                sql_exceptions.ArgumentError,
            ) as e:
                return {
                    "success": False,
                    "message": str(e),
                }
    return False


def selftools_db_update(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any]:
    tk.check_access("sysadmin", context, data_dict)

    if not utils.selftools_verify_operations_pwd(
        data_dict.get("selftools_pwd")
    ):
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
                    q = q.filter(
                        getattr(model_class, where_field) == where_value
                    )

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
                    return {
                        "success": False,
                        "message": "Provide the WHERE condition",
                    }
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
                    [
                        item.decode("utf-8")
                        for item in redis_conn.lrange(key, 0, 24)
                    ]
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

    if not utils.selftools_verify_operations_pwd(
        data_dict.get("selftools_pwd")
    ):
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

    if not utils.selftools_verify_operations_pwd(
        data_dict.get("selftools_pwd")
    ):
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

    if not utils.selftools_verify_operations_pwd(
        data_dict.get("selftools_pwd")
    ):
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
            {"key": ck, "value": tk.config.get(ck)}
            for ck in config_keys
            if key in ck
        ]
        return {"success": True, "results": config_results}

    return {"success": False}


def selftools_model_export(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any] | Literal[False]:
    tk.check_access("sysadmin", context, data_dict)

    if not utils.selftools_verify_operations_pwd(
        data_dict.get("selftools_pwd")
    ):
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
    columns = map(
        lambda key: data_dict.get(key, []), default_value_conditions_field
    )
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
                                    row,
                                    rel.mapper.class_,
                                    collector,
                                    default_models,
                                )
                                for row in rows
                            ]

            if c_r := [
                i
                for i in custom_relationships
                if i["local_model"] == model_name
            ]:
                for r in c_r:
                    r_m = [
                        m
                        for m in default_models
                        if m["label"] == r["remote_model"]
                    ]
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
                                _collect(
                                    row,
                                    remote_model,
                                    collector,
                                    default_models,
                                )
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

    if not utils.selftools_verify_operations_pwd(
        data_dict.get("selftools_pwd")
    ):
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
        r_obj = (
            model.Session.query(model_class)
            .filter(primary_key == obj_id)
            .first()
        )

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


def selftools_datastore_query(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any] | Literal[False]:
    """Query Datastore database to get list of resource IDs (table names)"""
    tk.check_access("sysadmin", context, data_dict)

    if not datastore_available:
        return {
            "success": False,
            "message": "Datastore plugin is not available",
        }

    search_query = data_dict.get("q", "").strip()
    orphaned_only = tk.asbool(data_dict.get("orphaned_only", False))
    limit = int(data_dict.get("limit", 100))
    batch_size = 1000

    try:
        if get_read_engine is None:
            return {
                "success": False,
                "message": "Datastore plugin is not available",
            }

        engine = get_read_engine()

        with engine.connect() as connection:
            tables_with_counts = []

            if orphaned_only:
                offset = 0

                while len(tables_with_counts) < limit:
                    # Get next batch of tables
                    if search_query:
                        query = text(
                            """
                            SELECT table_name
                            FROM information_schema.tables
                            WHERE table_schema = 'public'
                            AND table_type = 'BASE TABLE'
                            AND table_name NOT LIKE '\\_%'
                            AND table_name LIKE :search_pattern
                            ORDER BY table_name
                            LIMIT :batch_size OFFSET :offset
                        """
                        )
                        result = connection.execute(
                            query,
                            {
                                "search_pattern": f"%{search_query}%",
                                "batch_size": batch_size,
                                "offset": offset,
                            },
                        )
                    else:
                        query = text(
                            """
                            SELECT table_name
                            FROM information_schema.tables
                            WHERE table_schema = 'public'
                            AND table_type = 'BASE TABLE'
                            AND table_name NOT LIKE '\\_%'
                            ORDER BY table_name
                            LIMIT :batch_size OFFSET :offset
                        """
                        )
                        result = connection.execute(
                            query, {"batch_size": batch_size, "offset": offset}
                        )

                    batch_tables = [row[0] for row in result]

                    if not batch_tables:
                        break

                    for table in batch_tables:
                        if len(tables_with_counts) >= limit:
                            break

                        try:
                            resource = model.Resource.get(table)
                            resource_exists = bool(resource)

                            if resource_exists:
                                continue

                            count_query = text(
                                f'SELECT COUNT(*) FROM "{table}"'
                            )
                            count_result = connection.execute(count_query)
                            record_count = count_result.scalar()

                            tables_with_counts.append(
                                {
                                    "table_name": table,
                                    "record_count": record_count,
                                    "resource_exists": False,
                                }
                            )
                        except Exception as e:
                            log.warning(
                                "Error processing table %s: %s", table, repr(e)
                            )

                    offset += batch_size

                    if len(tables_with_counts) >= limit:
                        break
            else:
                # Normal mode - simple limit query
                if search_query:
                    query = text(
                        """
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_type = 'BASE TABLE'
                        AND table_name NOT LIKE '\\_%'
                        AND table_name LIKE :search_pattern
                        ORDER BY table_name
                        LIMIT :limit
                    """
                    )
                    result = connection.execute(
                        query,
                        {
                            "search_pattern": f"%{search_query}%",
                            "limit": limit,
                        },
                    )
                else:
                    query = text(
                        """
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_type = 'BASE TABLE'
                        AND table_name NOT LIKE '\\_%'
                        ORDER BY table_name
                        LIMIT :limit
                    """
                    )
                    result = connection.execute(query, {"limit": limit})

                tables = [row[0] for row in result]

                # Get record count and check resource existence
                for table in tables:
                    try:
                        count_query = text(f'SELECT COUNT(*) FROM "{table}"')
                        count_result = connection.execute(count_query)
                        record_count = count_result.scalar()

                        # Check if resource exists in CKAN
                        resource = model.Resource.get(table)
                        resource_exists = bool(resource)

                        tables_with_counts.append(
                            {
                                "table_name": table,
                                "record_count": record_count,
                                "resource_exists": resource_exists,
                            }
                        )
                    except Exception as e:
                        log.warning(
                            "Error counting records in table %s: %s",
                            table,
                            repr(e),
                        )
                        tables_with_counts.append(
                            {
                                "table_name": table,
                                "record_count": 0,
                                "resource_exists": False,
                            }
                        )

            return {
                "success": True,
                "total_tables": len(tables_with_counts),
                "tables": tables_with_counts,
                "search_query": search_query if search_query else None,
                "orphaned_only": orphaned_only,
            }
    except Exception as e:
        log.error("Datastore query error: %s", repr(e))
        return {
            "success": False,
            "message": "Error: " + str(e),
        }


def selftools_datastore_table_data(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any] | Literal[False]:
    """Get data from specific Datastore table"""
    tk.check_access("sysadmin", context, data_dict)

    if not datastore_available:
        return {
            "success": False,
            "message": "Datastore plugin is not available",
        }

    table_id = data_dict.get("table_id", "").strip()
    limit = int(data_dict.get("limit", 100))
    filter_column = data_dict.get("filter_column", "").strip()
    filter_value = data_dict.get("filter_value", "").strip()

    if not table_id:
        return {
            "success": False,
            "message": "Table ID is required",
        }

    try:
        if get_read_engine is None:
            return {
                "success": False,
                "message": "Datastore plugin is not available",
            }

        engine = get_read_engine()

        with engine.connect() as connection:
            # Get column names and types
            columns_query = text(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = :table_name
                ORDER BY ordinal_position
            """
            )
            columns_result = connection.execute(
                columns_query, {"table_name": table_id}
            )

            columns = []
            column_types = {}
            for row in columns_result:
                col_name = row[0]
                col_type = row[1]
                columns.append(col_name)
                column_types[col_name] = col_type

            if filter_column and filter_value and filter_column in columns:
                data_query = text(
                    f'SELECT * FROM "{table_id}" WHERE "{filter_column}" = :filter_value LIMIT :limit'
                )
                data_result = connection.execute(
                    data_query, {"filter_value": filter_value, "limit": limit}
                )
            else:
                data_query = text(f'SELECT * FROM "{table_id}" LIMIT :limit')
                data_result = connection.execute(data_query, {"limit": limit})

            results = []
            for row in data_result:
                row_values = []
                for col in columns:
                    value = row._mapping.get(col)
                    if value is not None:
                        row_values.append(value)
                    else:
                        row_values.append("")
                results.append(row_values)

            # Try to get resource info from CKAN
            resource_url = None
            resource_name = None
            try:
                resource = model.Resource.get(table_id)
                if resource:
                    resource_url = tk.h.url_for(
                        "resource.read",
                        id=resource.package_id,
                        resource_id=table_id,
                        _external=True,
                    )
                    resource_name = resource.name
            except Exception:
                pass

            return {
                "success": True,
                "table_id": table_id,
                "resource_url": resource_url,
                "resource_name": resource_name,
                "fields": columns,
                "field_types": column_types,
                "results": results,
                "total_records": limit,
                "filter_column": (
                    filter_column
                    if filter_column and filter_column in columns
                    else None
                ),
                "filter_value": (
                    filter_value
                    if filter_column and filter_column in columns
                    else None
                ),
            }
    except Exception as e:
        log.error("Datastore table data error: %s", repr(e))
        return {
            "success": False,
            "message": str(e),
        }


def selftools_datastore_delete(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any]:
    """Delete a table from Datastore"""
    tk.check_access("sysadmin", context, data_dict)

    if not utils.selftools_verify_operations_pwd(
        data_dict.get("selftools_pwd")
    ):
        return {"success": False, "message": "Unauthorized action."}

    table_id = data_dict.get("table_id", "").strip()

    if not table_id:
        return {
            "success": False,
            "message": "Table ID is required",
        }

    try:
        tk.get_action("datastore_delete")(
            context, {"resource_id": table_id, "force": True}
        )

        return {
            "success": True,
            "message": f"Table {table_id} deleted successfully",
            "deleted_table": table_id,
        }
    except Exception as e:
        log.error("Datastore delete error: %s", repr(e))
        return {
            "success": False,
            "message": str(e),
        }


def selftools_user_deleted(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any]:
    """Get all deleted users sorted by deletion date."""
    tk.check_access("sysadmin", context, data_dict)

    # Verify operations password
    if not utils.selftools_verify_operations_pwd(
        data_dict.get("selftools_pwd")
    ):
        return {
            "success": False,
            "message": "Unauthorized action.",
            "users": [],
            "count": 0,
        }

    limit = int(data_dict.get("limit", 100))
    max_limit = config.selftools_get_operations_limit()

    if limit > max_limit:
        limit = max_limit

    try:
        # Query for deleted users (state='deleted'), ordered by created date descending
        q = (
            model.Session.query(model.User)
            .filter(model.User.state == "deleted")
            .order_by(model.User.created.desc())
        )

        if limit:
            q = q.limit(limit)

        deleted_users = q.all()

        users_list = []
        for user in deleted_users:
            users_list.append(
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email if user.email else "",
                    "fullname": user.fullname if user.fullname else "",
                    "created": (
                        user.created.isoformat() if user.created else ""
                    ),
                    "state": user.state,
                    "sysadmin": user.sysadmin,
                }
            )

        return {
            "success": True,
            "users": users_list,
            "count": len(users_list),
        }
    except Exception as e:
        log.error("User deleted query error: %s", repr(e))
        return {
            "success": False,
            "message": str(e),
            "users": [],
            "count": 0,
        }


def selftools_user_add(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add a new user with optional extra fields."""
    tk.check_access("sysadmin", context, data_dict)

    # Verify operations password
    if not utils.selftools_verify_operations_pwd(
        data_dict.get("selftools_pwd")
    ):
        return {
            "success": False,
            "message": "Unauthorized action.",
        }

    # Get required fields
    username = data_dict.get("username", "").strip()
    email = data_dict.get("email", "").strip()
    password = data_dict.get("password", "")
    password_confirm = data_dict.get("password_confirm", "")

    # Validate required fields
    if not username:
        return {
            "success": False,
            "message": "Username is required.",
        }

    if not email:
        return {
            "success": False,
            "message": "Email is required.",
        }

    if not password:
        return {
            "success": False,
            "message": "Password is required.",
        }

    # Validate password match
    if password != password_confirm:
        return {
            "success": False,
            "message": "Passwords do not match.",
        }

    # Build user dict with standard fields
    user_dict = {
        "name": username,
        "email": email,
        "password": password,
    }

    # Add optional fullname
    fullname = data_dict.get("fullname", "").strip()
    if fullname:
        user_dict["fullname"] = fullname

    # Parse and add extra fields from JSON
    extra_fields_json = data_dict.get("extra_fields", "").strip()
    if extra_fields_json:
        try:
            extra_fields = json.loads(extra_fields_json)
            if not isinstance(extra_fields, dict):
                return {
                    "success": False,
                    "message": "Extra fields must be a JSON object (dictionary).",
                }
            # Merge extra fields into user_dict
            user_dict.update(extra_fields)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "message": f"Invalid JSON in extra fields: {str(e)}",
            }

    try:
        # Create user using CKAN's user_create action
        new_user = tk.get_action("user_create")(context, user_dict)

        return {
            "success": True,
            "message": f"User created successfully with ID: {new_user.get('id')}",
            "user_id": new_user.get("id"),
            "username": new_user.get("name"),
        }
    except tk.ValidationError as e:
        error_message = (
            str(e.error_dict) if hasattr(e, "error_dict") else str(e)
        )
        return {
            "success": False,
            "message": f"Validation error: {error_message}",
        }
    except Exception as e:
        log.error("User add error: %s", repr(e))
        return {
            "success": False,
            "message": f"Error creating user: {str(e)}",
        }


def selftools_user_info(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any]:
    """Get user information with counts for packages, organizations, and groups."""
    tk.check_access("sysadmin", context, data_dict)

    # Verify operations password
    if not utils.selftools_verify_operations_pwd(
        data_dict.get("selftools_pwd")
    ):
        return {
            "success": False,
            "message": "Unauthorized action.",
        }

    user_identifier = data_dict.get("user_identifier", "").strip()
    if not user_identifier:
        return {
            "success": False,
            "message": "Username or ID is required.",
        }

    try:
        # Try to get user by name or id
        user = model.User.get(user_identifier)

        if not user:
            return {
                "success": False,
                "message": f"User '{user_identifier}' not found.",
            }

        # Get package count
        package_count = (
            model.Session.query(model.Package)
            .filter(
                model.Package.creator_user_id == user.id,
                model.Package.state != "deleted",
            )
            .count()
        )

        # Get organization count using organization_list_for_user action
        orgs = tk.get_action("organization_list_for_user")(
            context, {"id": user.id, "permission": "read"}
        )
        org_count = len(orgs) if orgs else 0

        # Get group count using group_list_for_user action
        groups = tk.get_action(
            selfinfo_config.selfinfo_get_actions_prefix()
            + "selfinfo_group_list_for_user"
        )(context, {"id": user.id, "permission": "read"})
        group_count = len(groups) if groups else 0

        # Get follows count
        follows = tk.get_action("followee_list")(context, {"id": user.id})
        follows_count = len(follows) if follows else 0

        # Get collaborator count (only if feature is enabled)
        collaborator_count = 0
        collaborators_enabled = tk.asbool(
            tk.config.get("ckan.auth.allow_dataset_collaborators", False)
        )
        if collaborators_enabled:
            try:
                collaborators = tk.get_action(
                    "package_collaborator_list_for_user"
                )(context, {"id": user.id})
                collaborator_count = len(collaborators) if collaborators else 0
            except Exception:
                collaborator_count = 0

        return {
            "success": True,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email if user.email else "",
                "fullname": user.fullname if user.fullname else "",
                "created": user.created.isoformat() if user.created else "",
                "state": user.state,
                "sysadmin": user.sysadmin,
            },
            "package_count": package_count,
            "org_count": org_count,
            "group_count": group_count,
            "follows_count": follows_count,
            "collaborator_count": collaborator_count,
            "collaborators_enabled": collaborators_enabled,
        }
    except Exception as e:
        log.error("User info query error: %s", repr(e))
        return {
            "success": False,
            "message": str(e),
        }


def selftools_user_packages(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any]:
    """Get all packages created by a user."""
    tk.check_access("sysadmin", context, data_dict)

    user_id = data_dict.get("user_id", "").strip()
    if not user_id:
        return {"packages": []}

    try:
        packages = (
            model.Session.query(model.Package)
            .filter(
                model.Package.creator_user_id == user_id,
                model.Package.state != "deleted",
            )
            .all()
        )

        packages_list = []
        for pkg in packages:
            packages_list.append(
                {
                    "name": pkg.name,
                    "title": pkg.title if pkg.title else pkg.name,
                    "state": pkg.state,
                    "type": pkg.type,
                    "private": pkg.private,
                    "metadata_created": (
                        pkg.metadata_created.isoformat()
                        if pkg.metadata_created
                        else ""
                    ),
                }
            )

        return {"packages": packages_list}
    except Exception as e:
        log.error("User packages query error: %s", repr(e))
        return {"packages": []}


def selftools_user_organizations(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any]:
    """Get all organizations for a user with their roles."""
    tk.check_access("sysadmin", context, data_dict)

    user_id = data_dict.get("user_id", "").strip()
    if not user_id:
        return {"organizations": []}

    try:
        # Use organization_list_for_user action
        orgs = tk.get_action("organization_list_for_user")(
            context,
            {
                "id": user_id,
                "permission": "read",
                "include_dataset_count": True,
            },
        )

        return {"organizations": orgs if orgs else []}
    except Exception as e:
        log.error("User organizations query error: %s", repr(e))
        return {"organizations": []}


def selftools_user_groups(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any]:
    """Get all groups for a user with their roles."""
    tk.check_access("sysadmin", context, data_dict)

    user_id = data_dict.get("user_id", "").strip()
    if not user_id:
        return {"groups": []}

    try:
        # Use custom selfinfo_group_list_for_user action
        groups = tk.get_action(
            selfinfo_config.selfinfo_get_actions_prefix()
            + "selfinfo_group_list_for_user"
        )(
            context,
            {
                "id": user_id,
                "permission": "read",
                "include_dataset_count": True,
            },
        )

        return {"groups": groups if groups else []}
    except Exception as e:
        log.error("User groups query error: %s", repr(e))
        return {"groups": []}


def selftools_user_follows(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any]:
    """Get all entities that a user follows."""
    tk.check_access("sysadmin", context, data_dict)

    user_id = data_dict.get("user_id", "").strip()
    if not user_id:
        return {"follows": []}

    try:
        # Use followee_list action to get what user follows
        follows = tk.get_action("followee_list")(context, {"id": user_id})

        return {"follows": follows if follows else []}
    except Exception as e:
        log.error("User follows query error: %s", repr(e))
        return {"follows": []}


def selftools_user_collaborators(
    context: types.Context, data_dict: dict[str, Any]
) -> dict[str, Any]:
    """Get all datasets where user is a collaborator."""
    tk.check_access("sysadmin", context, data_dict)

    user_id = data_dict.get("user_id", "").strip()
    if not user_id:
        return {"collaborators": [], "enabled": False}

    # Check if collaborators feature is enabled
    collaborators_enabled = tk.asbool(
        tk.config.get("ckan.auth.allow_dataset_collaborators", False)
    )

    if not collaborators_enabled:
        return {"collaborators": [], "enabled": False}

    try:
        # Use package_collaborator_list_for_user action
        collaborators = tk.get_action("package_collaborator_list_for_user")(
            context, {"id": user_id}
        )

        # Enrich with package details
        enriched_collaborators = []
        for collab in collaborators if collaborators else []:
            try:
                pkg = model.Package.get(collab.get("package_id"))
                if pkg:
                    enriched_collaborators.append(
                        {
                            "package_id": collab.get("package_id"),
                            "package_name": pkg.name,
                            "package_title": (
                                pkg.title if pkg.title else pkg.name
                            ),
                            "capacity": collab.get("capacity"),
                            "modified": collab.get("modified"),
                        }
                    )
            except Exception:
                # If package not found, still add basic info
                enriched_collaborators.append(
                    {
                        "package_id": collab.get("package_id"),
                        "package_name": collab.get("package_id"),
                        "package_title": collab.get("package_id"),
                        "capacity": collab.get("capacity"),
                        "modified": collab.get("modified"),
                    }
                )

        return {"collaborators": enriched_collaborators, "enabled": True}
    except Exception as e:
        log.error("User collaborators query error: %s", repr(e))
        return {"collaborators": [], "enabled": True}


def selfinfo_group_list_for_user(
    context: types.Context, data_dict: dict[str, Any]
) -> list[dict[str, Any]]:
    """
    Return the groups that the user has a given permission for.

    Similar to organization_list_for_user but for groups instead of organizations.

    :param id: the name or id of the user to get the group list for
    :param permission: the permission the user has against the returned groups
        (optional, default: "manage_group")
    :param include_dataset_count: include the package_count in each group
        (optional, default: False)

    :returns: list of groups that the user has the given permission for
    """
    from ckan import authz
    from ckan.lib.dictization import model_dictize
    from ckan.common import asbool

    if data_dict.get("id"):
        user_obj = model.User.get(data_dict["id"])
        if not user_obj:
            raise tk.ObjectNotFound
        user = user_obj.name
    else:
        user = context["user"]

    tk.check_access("sysadmin", context, data_dict)
    sysadmin = authz.is_sysadmin(user)

    groups_q = (
        model.Session.query(model.Group)
        .filter(model.Group.is_organization.is_(False))
        .filter(model.Group.state == "active")
    )

    if sysadmin:
        groups_and_capacities = [(group, "admin") for group in groups_q.all()]
    else:
        # for non-Sysadmins check they have the required permission
        permission = data_dict.get("permission", "manage_group")
        roles = authz.get_roles_with_permission(permission)

        if not roles:
            return []
        user_id = authz.get_user_id_for_username(user, allow_none=True)
        if not user_id:
            return []

        q = (
            model.Session.query(model.Member, model.Group)
            .filter(model.Member.table_name == "user")
            .filter(model.Member.capacity.in_(roles))
            .filter(model.Member.table_id == user_id)
            .filter(model.Member.state == "active")
            .join(model.Group)
        )

        group_ids: set[str] = set()
        roles_that_cascade = authz.check_config_permission(
            "roles_that_cascade_to_sub_groups"
        )
        group_ids_to_capacities: dict[str, str] = {}

        for member, group in q.all():
            if member.capacity in roles_that_cascade:
                children_group_ids = [
                    grp_tuple[0]
                    for grp_tuple in group.get_children_group_hierarchy(
                        type="group"
                    )
                ]
                for group_id in children_group_ids:
                    group_ids_to_capacities[group_id] = member.capacity
                group_ids |= set(children_group_ids)

            group_ids_to_capacities[group.id] = member.capacity
            group_ids.add(group.id)

        if not group_ids:
            return []

        groups_q = groups_q.filter(model.Group.id.in_(group_ids))
        groups_and_capacities = [
            (group, group_ids_to_capacities[group.id])
            for group in groups_q.all()
        ]

    context["with_capacity"] = True
    groups_list = model_dictize.group_list_dictize(
        groups_and_capacities,
        context,
        with_package_counts=asbool(data_dict.get("include_dataset_count")),
        with_member_counts=asbool(data_dict.get("include_member_count")),
    )
    return groups_list

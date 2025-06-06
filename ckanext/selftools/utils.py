from __future__ import annotations

import logging

from typing import Any
import ckan.model as model
import ckan.plugins as p

from ckanext.selftools import interfaces
from ckanext.selftools.config import (
    selftools_get_operations_pwd,
    selftools_get_categories_list,
    selftools_get_tools_blacklist,
)

log = logging.getLogger(__name__)

SELFTOOLS_TOOLS = [
    {
        "key": "solr",
        "label": "Solr",
        "tools": [
            {
                "key": "solr_query",
                "label": "Query",
                "snippet": "/selftools/tools/solr/solr_query.html",
            },
            {
                "key": "solr_index",
                "label": "Index",
                "snippet": "/selftools/tools/solr/solr_index.html",
            },
            {
                "key": "solr_delete",
                "label": "Delete",
                "snippet": "/selftools/tools/solr/solr_delete.html",
            },
        ],
    },
    {
        "key": "db",
        "label": "DB",
        "tools": [
            {
                "key": "db_query",
                "label": "Query",
                "snippet": "/selftools/tools/db/db_query.html",
            },
            {
                "key": "db_update",
                "label": "Update",
                "snippet": "/selftools/tools/db/db_update.html",
            },
        ],
    },
    {
        "key": "redis",
        "label": "Redis",
        "tools": [
            {
                "key": "redis_query",
                "label": "Query",
                "snippet": "/selftools/tools/redis/redis_query.html",
            },
            {
                "key": "redis_update",
                "label": "Update/Create",
                "snippet": "/selftools/tools/redis/redis_update.html",
            },
            {
                "key": "redis_delete",
                "label": "Delete",
                "snippet": "/selftools/tools/redis/redis_delete.html",
            },
        ],
    },
    {
        "key": "config",
        "label": "Config",
        "tools": [
            {
                "key": "config_query",
                "label": "Query",
                "snippet": "/selftools/tools/config/config_query.html",
            },
        ],
    },
    {
        "key": "model",
        "label": "Model",
        "tools": [
            {
                "key": "model_export",
                "label": "Export",
                "snippet": "/selftools/tools/model/model_export.html",
            },
            {
                "key": "model_import",
                "label": "Import",
                "snippet": "/selftools/tools/model/model_import.html",
            },
        ],
    },
]


def get_db_models() -> list[dict[str, Any]]:
    try:
        models = [
            model.Package,
            model.PackageExtra,
            model.PackageTag,
            model.Tag,
            model.Resource,
            model.ResourceView,
            model.User,
            model.Group,
            model.Member,
            model.PackageMember,
            model.Vocabulary,
            model.SystemInfo,
        ]

        # models modification
        for item in p.PluginImplementations(interfaces.ISelftools):
            item.selftools_db_models(models)

        return [{"label": model.__name__, "model": model} for model in models]
    except Exception:
        log.error("Cannot retrieve DB Models.")

    return [{}]


def get_selftools_categories() -> list[dict[str, Any]]:
    tools_blacklist = selftools_get_tools_blacklist()

    def _filter_tools(category: dict[str, Any]) -> dict[str, Any]:
        tools = category.get("tools")
        if tools_blacklist and tools:
            for tb in tools_blacklist:
                tb = tb.strip().split(".")
                if category["key"] == tb[0]:
                    tools = [t for t in tools if t["key"] != tb[1]]
            category["tools"] = tools
        return category

    categories = [
        _filter_tools(c)
        for c in SELFTOOLS_TOOLS
        if c["key"] in selftools_get_categories_list()
    ]

    return categories


def selftools_verify_operations_pwd(pwd: str | None) -> bool:
    config_pwd = selftools_get_operations_pwd()
    if not config_pwd:
        return True

    if config_pwd and pwd and (config_pwd == pwd):
        return True

    return False

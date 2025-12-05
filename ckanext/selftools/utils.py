from __future__ import annotations

import logging
from typing import Any

import ckan.plugins as p
from ckan.model.domain_object import DomainObject
from ckan.model.base import BaseModel

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
        "icon": "fas fa-search",
        "tools": [
            {
                "key": "solr_query",
                "label": "Query",
                "snippet": "/selftools/tools/solr/solr_query.html",
                "icon": "fas fa-search",
            },
            {
                "key": "solr_index",
                "label": "Index",
                "snippet": "/selftools/tools/solr/solr_index.html",
                "icon": "fas fa-upload",
            },
            {
                "key": "solr_delete",
                "label": "Delete",
                "snippet": "/selftools/tools/solr/solr_delete.html",
                "icon": "fas fa-trash-alt",
            },
        ],
    },
    {
        "key": "db",
        "label": "DB",
        "icon": "fas fa-database",
        "tools": [
            {
                "key": "db_query",
                "label": "Query",
                "snippet": "/selftools/tools/db/db_query.html",
                "icon": "fas fa-search",
            },
            {
                "key": "db_update",
                "label": "Update",
                "snippet": "/selftools/tools/db/db_update.html",
                "icon": "fas fa-edit",
            },
        ],
    },
    {
        "key": "redis",
        "label": "Redis",
        "icon": "fas fa-memory",
        "tools": [
            {
                "key": "redis_query",
                "label": "Query",
                "snippet": "/selftools/tools/redis/redis_query.html",
                "icon": "fas fa-search",
            },
            {
                "key": "redis_update",
                "label": "Update/Create",
                "snippet": "/selftools/tools/redis/redis_update.html",
                "icon": "fas fa-edit",
            },
            {
                "key": "redis_delete",
                "label": "Delete",
                "snippet": "/selftools/tools/redis/redis_delete.html",
                "icon": "fas fa-trash",
            },
        ],
    },
    {
        "key": "config",
        "label": "Config",
        "icon": "fas fa-cogs",
        "tools": [
            {
                "key": "config_query",
                "label": "Query",
                "snippet": "/selftools/tools/config/config_query.html",
                "icon": "fas fa-search",
            },
        ],
    },
    {
        "key": "model",
        "label": "Model",
        "icon": "fab fa-python",
        "tools": [
            {
                "key": "model_export",
                "label": "Export",
                "snippet": "/selftools/tools/model/model_export.html",
                "icon": "fas fa-file-export",
            },
            {
                "key": "model_import",
                "label": "Import",
                "snippet": "/selftools/tools/model/model_import.html",
                "icon": "fas fa-file-import",
            },
        ],
    },
    {
        "key": "datastore",
        "label": "Datastore",
        "icon": "fas fa-table",
        "tools": [
            {
                "key": "datastore_query",
                "label": "Data",
                "snippet": "/selftools/tools/datastore/datastore_query.html",
                "icon": "fas fa-database",
            },
        ],
    },
]


def get_db_models() -> list[dict[str, Any]]:
    try:
        exclude = ["System"]
        ckan_core_models = DomainObject.__subclasses__()
        custom_ckan_models = BaseModel.__subclasses__()
        models = ckan_core_models if ckan_core_models else []
        models.extend(custom_ckan_models if ckan_core_models else [])

        # models modification
        for item in p.PluginImplementations(interfaces.ISelftools):
            item.selftools_db_models(models)

        return [
            {"label": m.__name__, "model": m}
            for m in models
            if m.__name__ not in exclude
        ]
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

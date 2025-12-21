from __future__ import annotations

from typing import Any

from . import action
from ckanext.selfinfo import config


def get_actions():
    prefix = config.selfinfo_get_actions_prefix()

    actions: dict[str, Any] = {
        f"{prefix}selftools_solr_query": action.selftools_solr_query,
        f"{prefix}selftools_solr_delete": action.selftools_solr_delete,
        f"{prefix}selftools_solr_index": action.selftools_solr_index,
        f"{prefix}selftools_db_query": action.selftools_db_query,
        f"{prefix}selftools_db_update": action.selftools_db_update,
        f"{prefix}selftools_redis_query": action.selftools_redis_query,
        f"{prefix}selftools_redis_update": action.selftools_redis_update,
        f"{prefix}selftools_redis_delete": action.selftools_redis_delete,
        f"{prefix}selftools_config_query": action.selftools_config_query,
        f"{prefix}selftools_model_export": action.selftools_model_export,
        f"{prefix}selftools_model_import": action.selftools_model_import,
        f"{prefix}selftools_datastore_query": action.selftools_datastore_query,
        f"{prefix}selftools_datastore_table_data": action.selftools_datastore_table_data,
        f"{prefix}selftools_datastore_delete": action.selftools_datastore_delete,
        f"{prefix}selftools_user_add": action.selftools_user_add,
        f"{prefix}selftools_user_deleted": action.selftools_user_deleted,
        f"{prefix}selftools_user_info": action.selftools_user_info,
        f"{prefix}selftools_user_packages": action.selftools_user_packages,
        f"{prefix}selftools_user_organizations": action.selftools_user_organizations,
        f"{prefix}selftools_user_groups": action.selftools_user_groups,
        f"{prefix}selftools_user_follows": action.selftools_user_follows,
        f"{prefix}selftools_user_collaborators": action.selftools_user_collaborators,
        f"{prefix}selfinfo_group_list_for_user": action.selfinfo_group_list_for_user,
    }

    return actions

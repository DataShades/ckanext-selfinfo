from __future__ import annotations

import ckan.plugins.toolkit as tk


SELFTOOLS_CATEGORIES = "ckan.selftools.categories"
SELFTOOLS_OPERATIONS_PWD = "ckan.selftools.opetations_pwd"
SELFTOOLS_OPERATIONS_LIMIT = "ckan.selftools.operations_limit"
SELFTOOLS_CONFIG_BLACKLIST = "ckan.selftools.config_blacklist"
SELFTOOLS_TOOLS_BLACKLIST = "ckan.selftools.tools_blacklist"
SELFTOOLS_MODEL_FIELDS_BLACKLIST = "ckan.selftools.model_fields_blacklist"
SELFTOOLS_MODEL_ENCRYPTION_KEY = "ckan.selftools.model_key_ecryption"


def selftools_get_categories_list():
    return tk.config.get(SELFTOOLS_CATEGORIES)


def selftools_get_operations_pwd():
    return tk.config.get(SELFTOOLS_OPERATIONS_PWD)


def selftools_get_operations_limit():
    return tk.config.get(SELFTOOLS_OPERATIONS_LIMIT)


def selftools_get_config_blacklist():
    return tk.config.get(SELFTOOLS_CONFIG_BLACKLIST)


def selftools_get_tools_blacklist():
    return tk.config.get(SELFTOOLS_TOOLS_BLACKLIST)


def selftools_get_model_fields_blacklist():
    return tk.config.get(SELFTOOLS_MODEL_FIELDS_BLACKLIST)


def selftools_get_model_ecryption_key():
    return tk.config.get(SELFTOOLS_MODEL_ENCRYPTION_KEY)

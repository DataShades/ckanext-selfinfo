from __future__ import annotations
import logging
from typing import Any


from ckan import types
import ckan.plugins.toolkit as tk
import ckan.plugins as p

from ckanext.selfinfo import utils, interfaces, config

log = logging.getLogger(__name__)


@tk.side_effect_free
def get_selfinfo(
    context: types.Context,
    data_dict: dict[str, Any],
) -> dict[str, Any]:

    tk.check_access("sysadmin", context, data_dict)

    categories_to_show = config.selfinfo_get_categories()

    data_categories = utils.CATEGORIES

    log.debug("data_categories: %s", data_categories.keys())
    # If a list of categories is passed in, use that instead.
    if data_dict.get("categories"):
        categories = data_dict.get("categories")
        data_categories = {
            key: data_categories[key]
            for key in data_categories
            if not categories or key in categories
        }
        log.debug("data_categories dict filtered: %s", data_categories.keys())

    # filter categories if ckan config is set
    data = {
        key: func()
        for key, func in data_categories.items()
        if not categories_to_show or key in categories_to_show
    }
    log.debug("data_categories config filtered: %s", data_categories.keys())

    # data modification
    for item in p.PluginImplementations(interfaces.ISelfinfo):
        item.selfinfo_after_prepared(data)

    return data


def selfinfo_get_ram(
    context: types.Context,
    data_dict: dict[str, Any],
) -> dict[str, Any]:

    tk.check_access("sysadmin", context, data_dict)

    return utils.get_ram_usage()


@tk.side_effect_free
@tk.chained_action
def status_show(
    next_: types.Action, context: types.Context, data_dict: types.DataDict
) -> types.ActionResult.StatusShow:
    results = next_(context, data_dict)
    if "extensions" in results:
        results["extensions"] = [
            ext
            for ext in results["extensions"]
            if ext not in ["selfinfo", "selftools", "selftracking"]
        ]
    return results

from __future__ import annotations

import logging
import json
from typing import Any
import click
from prettytable import PrettyTable
from datetime import datetime

from ckan.lib.redis import connect_to_redis, Redis
import ckan.plugins.toolkit as tk

from ckanext.selfinfo import config, utils, helpers

log = logging.getLogger(__name__)


@click.argument("module", required=True)
def update_module_info(module: str):
    tk.get_action(helpers.selfinfo_action_name("update_last_module_check"))(
        {"ignore_auth": True},
        {
            "module": module,
        },
    )


def get_selfinfo():
    # TO DO
    # Remove or re-implement
    data = tk.get_action(config.selfinfo_get_main_action_name())(
        {"ignore_auth": True}, {}
    )

    platform_info: dict[str, Any] = data.get("platform_info", {})
    ram_usage: dict[str, Any] = data.get("ram_usage", {})
    platform_table = PrettyTable(
        ["System", "Python Version", "RAM Usage %", "RAM Usage GB"]
    )

    platform_table.add_row(
        [
            platform_info.get("platform"),
            platform_info.get("python_version"),
            ram_usage.get("precent_usage"),
            ram_usage.get("used_ram"),
        ]
    )
    click.echo(click.style("System Information", fg="green"))

    click.echo(platform_table)
    groups_order: list[dict[str, Any]] = [
        {"name": "ckan", "label": "CKAN"},
        {"name": "ckanext", "label": "CKANEXT"},
        {"name": "other", "label": "Other"},
    ]
    groups: dict[str, Any] = data.get("groups", {})

    for item in groups_order:
        click.echo(click.style(item["label"], fg="green"))
        item_table = PrettyTable(
            ["Name", "Current Version", "Possible Version", "Last Checked"]
        )

        for key, values in groups.get(item["name"], {}).items():
            log.debug("group details %s: %s, %r", item["name"], key, values)
            name = values.get("name")
            if name:
                item_table.add_row(
                    [
                        name,
                        values.get("current_version"),
                        values.get("latest_version"),
                        values.get("updated"),
                    ],
                    divider=True,
                )

        click.echo(item_table)


@click.argument("key", required=True)
@click.argument("label", required=False)
def write_selfinfo(key: str, label: str):
    expire_time = config.selfinfo_get_additional_profiles_expire_time()
    data = tk.get_action(config.selfinfo_get_main_action_name())(
        {"ignore_auth": True}, {}
    )
    data["label"] = label if label else key
    data["provided_on"] = datetime.utcnow().timestamp()
    redis: Redis = connect_to_redis()
    selfinfo_key = "selfinfo_" + key

    if expire_time:
        redis.set(selfinfo_key, json.dumps(data), ex=expire_time)
    else:
        redis.set(selfinfo_key, json.dumps(data))

    click.echo(f"Stored Selfinfo data under '{key}' key.")


def write_selfinfo_duplicated_env():
    expire_time = config.selfinfo_get_additional_profiles_expire_time()
    internal_ip = utils.selfinfo_retrieve_internal_ip()
    redis_prefix = config.selfinfo_get_redis_prefix()
    data = tk.get_action(config.selfinfo_get_main_action_name())(
        {"ignore_auth": True}, {}
    )
    data["label"] = f"{internal_ip} Env"
    data["provided_on"] = datetime.utcnow().timestamp()

    shared_categories = config.selfinfo_get_dulicated_envs_shared_categories()

    if shared_categories:
        for category in shared_categories:
            if category in data:
                del data[category]

    redis: Redis = connect_to_redis()
    selfinfo_key = (
        redis_prefix
        + "selfinfo_duplicated_env_"
        + internal_ip.replace(".", "_")
    )

    if expire_time:
        redis.set(selfinfo_key, json.dumps(data), ex=expire_time)
    else:
        redis.set(selfinfo_key, json.dumps(data))

    click.echo(f"Stored Selfinfo data under '{selfinfo_key}' key.")


@click.argument("key", required=True)
def delete_selfinfo_redis_key(key: str):
    resp = utils.selfinfo_delete_redis_key(key)
    if not resp:
        click.echo("This is not an selfinfo key.")
        raise click.Abort()
    click.echo(f"Deleted Selfinfo data under '{key}' key.")


def clear_packages_cache():
    """Clear all Python packages version cache from Redis."""
    try:
        from importlib.metadata import packages_distributions  # type: ignore[attr-defined]
    except ImportError:  # For Python<3.8
        from importlib_metadata import packages_distributions

    redis: Redis = connect_to_redis()
    pdistribs = packages_distributions()

    # Collect all package names
    all_modules = []
    for package_modules in pdistribs.values():
        all_modules.extend(package_modules)

    if not all_modules:
        click.echo("No packages found.")
        return

    click.echo(f"Found {len(all_modules)} packages in the system.")

    # Delete Redis keys for each package
    deleted_count = 0
    not_found_count = 0

    with click.progressbar(
        all_modules, label="Clearing package cache", show_pos=True
    ) as modules:
        for module in modules:
            redis_key = utils.get_redis_key(module)
            if redis.exists(redis_key):
                redis.delete(redis_key)
                deleted_count += 1
            else:
                not_found_count += 1

    click.echo(
        click.style(
            f"\n✓ Cleared cache for {deleted_count} packages.", fg="green"
        )
    )

    if not_found_count > 0:
        click.echo(
            click.style(
                f"  {not_found_count} packages had no cached data.",
                fg="yellow",
            )
        )

    click.echo(
        "\nNext time you visit the Python Modules page, "
        "latest versions will be fetched from PyPI."
    )

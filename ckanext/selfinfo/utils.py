from __future__ import annotations

import os
from typing import Any, Mapping, Optional, MutableMapping
import requests
import psutil
from psutil._common import bytes2human
import platform
import git
from git.exc import InvalidGitRepositoryError, NoSuchPathError
from datetime import datetime
import importlib_metadata as imetadata
import logging
import json
import distro
import inspect
import functools
import types
import socket
import click

from ckan.lib.redis import connect_to_redis, Redis
import ckan.plugins.toolkit as tk
from ckan.lib import jobs
from ckan.lib.search.common import (
    is_available as solr_available,
    make_connection as solr_connection,
)
from ckan.cli.cli import ckan as ckan_commands

from . import config, utils


log = logging.getLogger(__name__)


def get_redis_key(name: str) -> str:
    """
    Generate a Redis key by combining a prefix, the provided name, and a suffix.
    """
    return config.selfinfo_get_redis_prefix() + name + config.SELFINFO_REDIS_SUFFIX


def get_python_modules_info(force_reset: bool = False) -> dict[str, Any]:
    redis: Redis = connect_to_redis()
    now: float = datetime.utcnow().timestamp()

    groups: dict[str, Any] = {"ckan": {}, "ckanext": {}, "other": {}}
    pdistribs: Mapping[str, Any] = imetadata.packages_distributions()
    modules: dict[str, Any] = {p.name: p.version for p in imetadata.distributions()}

    for i, p in pdistribs.items():
        for module in p:
            group: str = i if i in groups else "other"

            if module not in groups[group]:
                redis_module_key: str = get_redis_key(module)
                data: MutableMapping[str, Any] = {
                    "name": module,
                    "current_version": modules.get(module, "unknown"),
                    "updated": now,
                }
                if not redis.hgetall(redis_module_key):
                    data["latest_version"] = get_lib_latest_version(module)
                    redis.hset(redis_module_key, mapping=dict(data))

                updated_time = redis.hget(redis_module_key, "updated")
                is_stale = True
                if updated_time:
                    updated_time = updated_time.decode("utf-8")  # type: ignore
                    is_stale = (now - float(updated_time)) > config.STORE_TIME
                if is_stale or force_reset:
                    log.debug(
                        "Updating module: %s due to isStale: %s, Force: %s",
                        module,
                        is_stale,
                        force_reset,
                    )
                    data["latest_version"] = get_lib_latest_version(module)
                    for key in data:
                        if data[key] != redis.hget(redis_module_key, key):
                            redis.hset(redis_module_key, key=key, value=data[key])

                groups[group][module] = {
                    k.decode("utf-8"): v.decode("utf-8")
                    for k, v in redis.hgetall(redis_module_key).items()  # type: ignore
                }

                # Convert the updated timestamp to a human-readable format
                groups[group][module]["updated"] = str(
                    datetime.fromtimestamp(float(groups[group][module]["updated"]))
                )

    # Sort specific groups alphabetically by module name
    groups["ckanext"] = dict(sorted(groups["ckanext"].items()))
    groups["other"] = dict(sorted(groups["other"].items()))

    return groups


def get_freeze() -> dict[str, "str|list[str]"]:
    try:
        from pip._internal.operations import freeze
    except ImportError:  # pip < 10.0
        from pip.operations import freeze  # type: ignore
    pkgs = freeze.freeze()
    pkgs = list(pkgs)
    pkgs_string = "\n".join(list(pkgs))
    return {
        "modules": pkgs,
        "modules_html": f"""{pkgs_string}""",
    }


def get_lib_data(lib: str) -> Optional[dict[str, Any]]:
    req = requests.get(
        config.PYPI_URL + lib + "/json",
        headers={"Content-Type": "application/json"},
    )

    if req.status_code == 200:
        return req.json()
    return None


def get_lib_latest_version(lib: str) -> str:
    data = get_lib_data(lib)

    if data and data.get("info"):
        return data["info"].get("version", "unknown")
    return "unknown"


def get_ram_usage() -> dict[str, Any]:
    psutil.process_iter.cache_clear()  # type: ignore cache_clear() is dynamic
    memory = psutil.virtual_memory()
    top10 = []
    processes = []
    for proc in psutil.process_iter(["pid", "name", "memory_info"]):
        try:
            mem = proc.info["memory_info"].rss
            processes.append((proc.info["pid"], proc.info["name"], mem))
            top10 = [
                list(process)
                for process in (
                    sorted(processes, key=lambda x: x[2], reverse=True)[:10]
                )
            ]

            for p in top10:
                p[2] = bytes2human(p[2])

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            log.error("Cannot retrieve processes")

    return {
        "precent_usage": memory.percent,
        "used_ram": bytes2human(memory.used),
        "total_ram": bytes2human(memory.total),
        "processes": top10,
    }


def get_disk_usage() -> list[dict[str, Any]]:
    paths = config.selfinfo_get_partitions()
    results = []

    for path in paths:
        # mounpoint
        try:
            usage = psutil.disk_usage(path.strip())
            if usage:
                results.append(
                    {
                        "path": path,
                        "precent_usage": usage.percent,
                        "total_disk": bytes2human(usage.total),
                        "free_space": bytes2human(usage.free),
                    }
                )
        except OSError:
            log.exception("Path '%s' does not exists.", path)
    return results


def get_platform_info() -> dict[str, Any]:
    return {
        "distro": distro.name() + " " + distro.version(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }


def gather_git_info() -> dict[str, "dict[str, Any]|list[dict[str, Any]]"]:
    ckan_repos_path = config.selfinfo_get_repos_path()
    git_info = {"repos_info": [], "access_errors": {}}
    if ckan_repos_path:
        ckan_repos = config.selfinfo_get_repos()
        list_repos = (
            ckan_repos
            if ckan_repos
            else [
                name
                for name in os.listdir(ckan_repos_path)
                if os.path.isdir(os.path.join(ckan_repos_path, name))
                and not name.startswith(".")
            ]
        )

        repos: dict[str, git.Repo | None] = {
            repo: get_git_repo(ckan_repos_path + "/" + repo)
            for repo in list_repos
            if repo
        }

        for name, repo in repos.items():
            if not repo:
                continue
            try:
                commit, branch = repo.head.object.name_rev.strip().split(" ")
                short_sha: str = repo.git.rev_parse(commit, short=True)
                on = "branch"

                if repo.head.is_detached and branch.startswith("remotes/"):
                    branch = short_sha
                    on = "commit"
                elif repo.head.is_detached and branch.startswith("tags/"):
                    on = "tag"
                elif repo.head.is_detached and (
                    not branch.startswith("tags/") and not branch.startswith("remotes/")
                ):
                    branch = short_sha
                    on = "commit"

                git_info["repos_info"].append(
                    {
                        "name": name,
                        "head": branch,
                        "commit": short_sha,
                        "on": on,
                        "remotes": [
                            {
                                "name": remote.name,
                                "url": remote.url,
                            }
                            for remote in repo.remotes
                        ],
                    }
                )
            except ValueError as e:
                git_info["access_errors"][name] = str(e)
    return git_info


def get_git_repo(path: str) -> Optional[git.Repo]:
    repo = None
    try:
        repo = git.Repo(path)
    except (InvalidGitRepositoryError, NoSuchPathError):
        log.debug("Git Collection failed", exc_info=True)
        pass

    return repo


def retrieve_errors() -> list[dict[str, Any]]:
    """Collection from function SelfinfoErrorHandler"""
    redis: Redis = connect_to_redis()
    key = get_redis_key("errors")
    data = []
    if not redis.exists(key):
        redis.set(key, json.dumps(data))  # init key
    else:
        raw = redis.get(key)
        data = json.loads(raw.decode("utf-8"))  # type: ignore
    return data


def ckan_actions() -> list[dict[str, Any]]:
    from ckan.logic import _actions

    data = []
    for n, f in _actions.items():
        chained = False
        # For chained items
        if hasattr(f, "__closure__") and f.__closure__ and len(f.__closure__):
            if isinstance(f.__closure__[0].cell_contents, functools.partial):
                chained = True

        data.append(
            {
                "func_name": n,
                "docstring": inspect.getdoc(f),
                "chained": chained,
            }
        )

    return data


def ckan_auth_actions() -> list[dict[str, Any]]:
    from ckan.authz import _AuthFunctions

    data = []
    for n in _AuthFunctions.keys():
        f = _AuthFunctions.get(n)
        chained = False
        # For chained items
        if isinstance(f, functools.partial):
            f = f.func
            chained = True

        data.append(
            {
                "func_name": n,
                "docstring": inspect.getdoc(f),
                "chained": chained,
            }
        )

    return data


def ckan_bluprints() -> dict[str, list[dict[str, Any]]]:
    from flask import current_app

    app = current_app
    data = {}
    try:
        for name, _ in app.blueprints.items():
            data[name] = []
            for rule in current_app.url_map.iter_rules():
                if rule.endpoint.startswith(f"{name}."):
                    view_func = current_app.view_functions[rule.endpoint]
                    # signature = inspect.signature(view_func)

                    data[name].append(
                        {
                            "path": rule.rule,
                            "methods": list(rule.methods or []),
                            "route": rule.endpoint,
                            "route_func": view_func.__name__,
                        }
                    )
    except RuntimeError:
        pass

    return data


def ckan_helpers() -> list[dict[str, Any]]:
    from ckan.lib.helpers import helper_functions

    data = []
    for n, f in helper_functions.items():
        chained = False
        # For chained items
        if isinstance(f, functools.partial):
            f = f.func
            chained = True

        # Avoid builtin
        if isinstance(f, (types.BuiltinFunctionType, types.BuiltinMethodType)):
            continue

        data.append(
            {
                "func_name": n,
                "docstring": inspect.getdoc(f),
                "defined": inspect.getsourcefile(f),
                "chained": chained,
            }
        )
    return data


def get_ckan_registered_cli() -> list[Any]:
    data = []
    if ckan_commands and ckan_commands.commands:

        def _get_command_info(cmd: click.Group | click.Command) -> dict[str, Any]:
            info = {
                "name": cmd.name,
                "help": cmd.help or "",
                "arguments": [],
                "options": [],
            }

            for param in cmd.params:
                param_info = {
                    "name": param.name,
                    "type": str(param.type),
                    "required": param.required,
                    "help": getattr(param, "help", ""),
                    "opts": getattr(param, "opts", []),
                }
                if isinstance(param, click.Argument):
                    info["arguments"].append(param_info)
                elif isinstance(param, click.Option):
                    info["options"].append(param_info)

            return info

        def _build_command_tree(group: click.Group) -> list[Any]:
            command_tree = []

            for _, cmd in group.commands.items():
                cmd_info: dict[str, Any] = _get_command_info(cmd)

                if isinstance(cmd, click.Group):
                    # recursively gather subcommands
                    cmd_info["subcommands"] = _build_command_tree(cmd)

                command_tree.append(cmd_info)

            return command_tree

        data = _build_command_tree(ckan_commands)

    return data


def get_status_show() -> Any:
    return tk.get_action("status_show")({}, {})


def get_ckan_queues() -> dict[str, dict[str, "str|list[dict[str, Any]]"]]:
    data = {}
    for queue in jobs.get_all_queues():
        jobs_counts = queue.count
        data[queue.name] = {
            "count": jobs_counts,
            "jobs": [jobs.dictize_job(job) for job in queue.get_jobs(0, 100)],
            "above_the_limit": True if jobs_counts > 100 else False,
        }

    return data


def get_solr_schema() -> dict[str, str]:
    data = {}
    schema_filename = config.selfinfo_get_solr_schema_filename()

    if solr_available() and schema_filename:
        try:
            solr = solr_connection()
            solr_url = solr.url

            schema_url = f"{solr_url.rstrip('/')}/admin/file"
            params = {
                "file": schema_filename,
                "contentType": "application/xml;charset=utf-8",
            }
            schema_response = requests.get(schema_url, params=params)
            schema_response.raise_for_status()

            data["schema"] = schema_response.text
        except requests.exceptions.HTTPError:
            log.exception("Solr Schema: Please re-check the filename you provided.")

    return data


def retrieve_additionals_redis_keys_info(key: str) -> dict[str, dict[str, Any]]:
    redis: Redis = connect_to_redis()
    data = {}
    try:
        selfinfo_key = "selfinfo_" + key
        raw = redis.get(selfinfo_key)
        if raw is not None:
            data = json.loads(raw.decode("utf-8"))  # type: ignore is syncronous
        if data.get("provided_on"):
            data["provided_on"] = str(datetime.fromtimestamp(data["provided_on"]))
    except TypeError:
        log.error("Cannot retrieve data using '%s' from Redis.", key)

    return data


def retrieve_additional_selfinfo_by_keys(key: str) -> dict[str, dict[str, Any]]:
    redis: Redis = connect_to_redis()
    try:
        selfinfo_key = key
        raw = redis.get(selfinfo_key)
        if raw is not None:
            data = json.loads(raw.decode("utf-8"))  # type: ignore
        else:
            data = {}

        if data.get("provided_on"):
            data["provided_on"] = str(datetime.fromtimestamp(data["provided_on"]))
    except TypeError:
        data = {}
        log.error("Cannot retrieve data using '%s' from Redis.", key)

    if config.selfinfo_get_dulicated_envs_mode():
        keys = selfinfo_internal_ip_keys()
        shared_categories = config.selfinfo_get_dulicated_envs_shared_categories()
        glob_categories = utils.CATEGORIES
        if shared_categories and key in keys:
            for category in shared_categories:
                if category in glob_categories and category not in data:
                    data[category] = glob_categories[category]()

    return data


def selfinfo_retrieve_internal_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"

    return ip


def selfinfo_internal_ip_keys() -> list[str]:
    redis: Redis = connect_to_redis()
    return [
        i.decode("utf-8") for i in redis.scan_iter(match="selfinfo_duplicated_env_*")
    ]


def selfinfo_delete_redis_key(key: str) -> bool:
    if not key.startswith("selfinfo_"):
        return False
    redis: Redis = connect_to_redis()
    selfinfo_key = key
    redis.delete(selfinfo_key)
    return True


CATEGORIES = {
    "python_modules": get_python_modules_info,
    "platform_info": get_platform_info,
    "ram_usage": get_ram_usage,
    "disk_usage": get_disk_usage,
    "git_info": gather_git_info,
    "freeze": get_freeze,
    "errors": retrieve_errors,
    "actions": ckan_actions,
    "auth_actions": ckan_auth_actions,
    "blueprints": ckan_bluprints,
    "helpers": ckan_helpers,
    "status_show": get_status_show,
    "ckan_queues": get_ckan_queues,
    "ckan_solr_schema": get_solr_schema,
    "ckan_cli_commands": get_ckan_registered_cli,
}

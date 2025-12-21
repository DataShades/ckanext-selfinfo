import click

from . import main


def get_commands():
    return [selfinfo]


@click.group()
def selfinfo():
    """ckanext-selfinfo management commands."""


selfinfo.command(main.update_module_info)
selfinfo.command(main.get_selfinfo)
selfinfo.command(main.write_selfinfo)
selfinfo.command(main.write_selfinfo_duplicated_env)
selfinfo.command(main.delete_selfinfo_redis_key)
selfinfo.command(main.clear_packages_cache)

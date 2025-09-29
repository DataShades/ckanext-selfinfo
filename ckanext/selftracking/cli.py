import click

import ckan.plugins.toolkit as tk


def get_commands():
    return [selftracking]


@click.group()
def selftracking():
    """selftracking management commands."""


@selftracking.command()
def store_tracking():
    """Store tracking that being gathered in Redis"""
    tk.get_action("selftracking_store_tracks")({"ignore_auth": True}, {})

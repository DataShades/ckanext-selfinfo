import click

import ckan.plugins.toolkit as tk
from ckanext.selfinfo import helpers


def get_commands():
    return [selftracking]


@click.group()
def selftracking():
    """selftracking management commands."""


@selftracking.command()
def store_tracking():
    """Store tracking that being gathered in Redis"""
    tk.get_action(helpers.selfinfo_action_name("selftracking_store_tracks"))(
        {"ignore_auth": True}, {}
    )

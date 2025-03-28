import ckan.plugins as plugins
import ckan.plugins.toolkit as tk

from .logic import action
from . import cli


@tk.blanket.cli(cli.get_commands)
@tk.blanket.actions(action.get_actions)
@tk.blanket.blueprints
class SelfinfoPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)

    # IConfigurer

    def update_config(self, config_):
        tk.add_template_directory(config_, "templates")
        tk.add_public_directory(config_, "public")
        tk.add_resource("assets", "selfinfo")

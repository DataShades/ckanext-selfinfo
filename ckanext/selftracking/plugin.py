from __future__ import annotations

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
from ckan.common import CKANConfig
import ckan.types as types

from .middleware import track_activity
from .cli import get_commands


@tk.blanket.config_declarations
@tk.blanket.actions
@tk.blanket.auth_functions
@tk.blanket.cli(get_commands)
@tk.blanket.helpers
class SelftrackingPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IMiddleware, inherit=True)

    # IConfigurer
    def update_config(self, config_: CKANConfig):
        tk.add_template_directory(config_, "templates")
        tk.add_public_directory(config_, "public")
        tk.add_resource("assets", "selftracking")

    # IMiddleware
    def make_middleware(self, app: types.CKANApp, _) -> types.CKANApp:
        app.after_request(track_activity)
        return app

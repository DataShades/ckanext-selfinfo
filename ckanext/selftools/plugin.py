from __future__ import annotations

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
from ckan.common import CKANConfig

from .logic import get_actions


@tk.blanket.config_declarations
@tk.blanket.actions(get_actions)
@tk.blanket.blueprints
@tk.blanket.helpers
class SelftoolsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)

    # IConfigurer

    def update_config(self, config_: CKANConfig):
        tk.add_template_directory(config_, "templates")
        tk.add_public_directory(config_, "public")
        tk.add_resource("assets", "selftools")

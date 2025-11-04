from __future__ import annotations
import logging
from datetime import datetime
from typing import Any
import pytest
import os

from ckan import model
import ckan.plugins.toolkit as tk
from ckan.tests.helpers import call_action
from ckan.tests import factories

from ckanext.selfinfo import config

log = logging.getLogger(__name__)

current_path: list[str] = os.getcwd().split("/")
current_path.pop()
updated_path: str = "/".join(current_path)


@pytest.mark.ckan_config("ckan.plugins", "selfinfo")
@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.selfinfo.ckan_repos_path", updated_path)
@pytest.mark.ckan_config("ckan.selfinfo.ckan_repos", "ckan ckanext-selfinfo")
class TestUPDATE:
    def test_update_last_module_check(self):
        user = factories.User()
        sysadmin = factories.Sysadmin()
        context: dict[str, Any] = {
            "model": model,
            "user": user["name"],
            "ignore_auth": False,
        }

        with pytest.raises(tk.NotAuthorized):
            call_action(
                config.selfinfo_get_main_action_name(), context=context
            )

        context["user"] = sysadmin["name"]
        selfinfo: dict[str, Any] = tk.get_action(
            config.selfinfo_get_main_action_name()
        )(context, {})
        assert "python_modules" in selfinfo, selfinfo.keys()
        assert "ckan" in selfinfo["python_modules"], selfinfo[
            "python_modules"
        ].keys()
        assert "ckan" in selfinfo["python_modules"]["ckan"], selfinfo[
            "python_modules"
        ]["ckan"].keys()

        ckan_info = selfinfo["python_modules"]["ckan"]["ckan"]

        updated: dict[str, Any] = tk.get_action("update_last_module_check")(
            context, {"module": "ckan"}
        )

        assert ckan_info != updated
        before_updated = datetime.fromisoformat(ckan_info["updated"])
        after_updated = datetime.fromisoformat(updated["updated"])
        assert before_updated < after_updated
        # pop update field, see that they are the same
        ckan_info.pop("updated", None)
        updated.pop("updated", None)
        assert ckan_info == updated

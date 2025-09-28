from __future__ import annotations

from typing import Any

from ckan.plugins import Interface


class ISelftracking(Interface):
    """Implement custom Selftracking response modification."""

    def selftracking_categories(self, categories: list[Any]) -> list[Any]:
        """Return list of categories.
        This method is called before returning the categories list.
        Useful if you want to add additional custom categories.
        :returns: list
        :rtype: list

        """

        return categories

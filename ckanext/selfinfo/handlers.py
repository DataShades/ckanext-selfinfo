from __future__ import annotations

import logging
import json

from ckan.lib.redis import connect_to_redis, Redis
import ckan.plugins.toolkit as tk

from .config import selfinfo_get_errors_limit
from .utils import get_redis_key


class SelfinfoErrorHandler(logging.Handler):
    """Custom handler to store exceptions."""

    def emit(self, record: logging.LogRecord):
        if record.levelno >= logging.ERROR:
            redis: Redis = connect_to_redis()
            log_message = self.format(record)
            redis_key = get_redis_key("errors")

            if not redis.exists(redis_key):
                redis.set(redis_key, json.dumps([]))

            errors = json.loads(redis.get(redis_key))  # pyright: ignore
            errors_limit = selfinfo_get_errors_limit()

            try:
                if len(errors) >= errors_limit:
                    start_key = len(errors) - errors_limit + 1
                    errors = errors[start_key:]
            except TypeError:
                # config_declaration is not initialized yet
                # so the app is not running
                # jump over the limit to store the error
                pass

            current_url = None
            try:
                current_url = tk.h.full_current_url()
            except (AttributeError, RuntimeError):
                pass

            errors.append(
                {
                    "error": log_message,
                    "error_url": current_url if current_url else "Missing URL",
                }
            )
            redis.set(redis_key, json.dumps(errors))

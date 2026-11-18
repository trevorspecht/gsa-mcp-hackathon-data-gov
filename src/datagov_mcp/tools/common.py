"""Tool-level error and output boundary, before framework exception conversion."""

import asyncio
import inspect
import json
import logging
import time
from functools import wraps

from datagov_mcp.errors import ServiceError


def guarded(function):
    @wraps(function)
    async def wrapper(*args, **kwargs):
        started = time.monotonic()
        code = "success"
        try:
            if inspect.iscoroutinefunction(function):
                result = await function(*args, **kwargs)
            else:
                result = await asyncio.to_thread(function, *args, **kwargs)
            if len(json.dumps(result, allow_nan=False).encode()) > 64_000:
                raise ServiceError(
                    "OUTPUT_LIMIT", "Tool output exceeds 64 KB", "Narrow the request"
                )
            return result
        except ServiceError as exc:
            code = exc.code
            return exc.as_dict()
        except Exception as exc:
            code = "INTERNAL_ERROR"
            logging.getLogger(__name__).error(
                "tool_failure type=%s", type(exc).__name__
            )
            return ServiceError(
                code,
                "Tool operation failed",
                "Ask the operator to inspect the server log",
            ).as_dict()
        finally:
            logging.getLogger(__name__).info(
                json.dumps(
                    {
                        "event": "tool_call",
                        "tool": function.__name__,
                        "outcome": code,
                        "elapsed_seconds": round(time.monotonic() - started, 3),
                    }
                )
            )

    return wrapper

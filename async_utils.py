import asyncio
import threading
from typing import Any, Coroutine, TypeVar

T = TypeVar("T")

def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """Run *coro* regardless of existing event loop state.

    If an event loop is already running, run the coroutine in a new loop.
    Otherwise, use the current loop. This avoids ``asyncio.run`` which
    fails when called from a running loop.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        result: dict[str, T] = {}

        def _run() -> None:
            inner_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(inner_loop)
            try:
                task = inner_loop.create_task(coro)
                result["value"] = inner_loop.run_until_complete(task)
            finally:
                inner_loop.close()

        thread = threading.Thread(target=_run)
        thread.start()
        thread.join()
        return result["value"]
    else:
        return loop.run_until_complete(coro)

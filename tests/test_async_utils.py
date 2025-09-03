import asyncio

from async_utils import run_async


async def sample_coro():
    await asyncio.sleep(0.01)
    return "done"


def test_run_async_without_running_loop():
    assert run_async(sample_coro()) == "done"


def test_run_async_with_existing_loop():
    results = []

    async def runner():
        results.append(run_async(sample_coro()))

    asyncio.run(runner())
    assert results == ["done"]

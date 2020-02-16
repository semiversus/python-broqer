import asyncio
import pytest

from broqer import Publisher, OnEmitFuture

from .eventloop import VirtualTimeEventLoop

@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()

def test_publisher():
    p = Publisher(1)
    future = OnEmitFuture(p, timeout=1, loop=asyncio.get_event_loop())

    assert future.result() == 1

    p.notify(2)
    assert future.result() == 1

@pytest.mark.asyncio
async def test_timeout(event_loop):
    p = Publisher()
    future = OnEmitFuture(p, timeout=0.01)
    await asyncio.sleep(0.05, loop=event_loop)

    with pytest.raises(asyncio.TimeoutError):
        future.result()

@pytest.mark.asyncio
async def test_cancel(event_loop):
    p = Publisher()
    future = OnEmitFuture(p, timeout=0.01)
    future.cancel()
    p.notify(1)

    with pytest.raises(asyncio.CancelledError):
        future.result()

def test_wrong_source():
    p = Publisher()
    on_emit_future = OnEmitFuture(p)

    with pytest.raises(ValueError):
        on_emit_future.emit(0, who=Publisher())
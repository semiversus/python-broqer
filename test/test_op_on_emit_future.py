import asyncio
import pytest

from broqer import Publisher, StatefulPublisher
from broqer.op import OnEmitFuture

from .eventloop import VirtualTimeEventLoop

@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()

def test_publisher():
    p = Publisher()
    future = p | OnEmitFuture()

    assert not future.done()

    p.notify(1)
    assert future.result() == 1

    p.notify(2)
    assert future.result() == 1

def test_stateful_publisher():
    p = StatefulPublisher(1)
    future = p | OnEmitFuture(timeout=1, loop=asyncio.get_event_loop())

    assert future.result() == 1

    p.notify(2)
    assert future.result() == 1

@pytest.mark.asyncio
async def test_timeout():
    p = Publisher()
    future = p | OnEmitFuture(timeout=0.01)
    await asyncio.sleep(0.05)

    with pytest.raises(asyncio.TimeoutError):
        future.result()

@pytest.mark.asyncio
async def test_cancel():
    p = Publisher()
    future = p | OnEmitFuture(timeout=0.01)
    future.cancel()
    p.notify(1)

    with pytest.raises(asyncio.CancelledError):
        future.result()

def test_wrong_source():
    p = Publisher()
    on_emit_future = OnEmitFuture()
    p | on_emit_future

    with pytest.raises(ValueError):
        on_emit_future.emit(0, who=Publisher())
import asyncio
import pytest
from unittest import mock

from broqer.publishers import PollPublisher
from broqer import Sink, NONE

from .eventloop import VirtualTimeEventLoop


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_subscribe(event_loop):
    poll_mock = mock.Mock(return_value=3)
    sink_mock = mock.Mock()

    p = PollPublisher(poll_mock, 1)

    await asyncio.sleep(1, loop=event_loop)
    assert p.get() is NONE

    p.subscribe(Sink(sink_mock))
    sink_mock.assert_called_once_with(3)
    poll_mock.assert_called_once()

    await asyncio.sleep(2.5, loop=event_loop)
    sink_mock.assert_called_with(3)
    assert sink_mock.call_count == 3
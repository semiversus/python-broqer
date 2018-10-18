from unittest import mock
import pytest

from broqer.op import Cache, Sink
from broqer import Publisher, StatefulPublisher, NONE

from .helper import check_single_operator

@pytest.mark.parametrize('args, input_vector, output_vector', [
    ((-1,), (0, 1, 2, 3), (0, 1, 2, 3)),
    ((-1,), (-1, -1, -1, -1), (NONE, NONE, NONE, NONE)),
    ((-1,), (1, 1, -1, -1), (1, NONE, -1, NONE)),
    (('a',), (0, 0, 'b', -1), (0, NONE, 'b', -1)),
    (((1,2),), ((1,2), (1,3), (1,3)), (NONE, (1,3), NONE)),
    ((), (0, 1, 2, 3), (0, 1, 2, 3)),
    ((), (-1, -1, -1, 1), (-1, NONE, NONE, 1)),
])
def test_with_publisher(args, input_vector, output_vector):
    init = args[0] if args else None
    check_single_operator(Cache, args, {}, input_vector, output_vector, initial_state=init, has_state=True)

def test_uninitialised_with_publisher():
    source = Publisher()
    dut = source | Cache()
    cb = mock.Mock()
    dut | Sink(cb)

    cb.assert_not_called()

    source.notify(1)
    cb.assert_called_once_with(1)

    source.notify(1)
    cb.assert_called_once_with(1)


def test_initialised_with_publisher():
    source = Publisher()
    dut = source | Cache(1)
    cb = mock.Mock()
    dut | Sink(cb)

    cb.assert_called_once_with(1)
    cb.reset_mock()

    source.notify(2)
    cb.assert_called_once_with(2)

    source.notify(2)
    cb.assert_called_once_with(2)

    with pytest.raises(ValueError):
        Publisher() | dut

def test_uninitialised_with_stateful():
    source = StatefulPublisher(1)
    dut = source | Cache()
    cb = mock.Mock()
    dut |Sink(cb)

    cb.assert_called_once_with(1)
    source.notify(1)
    cb.assert_called_once_with(1)

    cb.reset_mock()
    source.notify(2)

    cb.assert_called_once_with(2)

def test_initialised_with_stateful():
    source = StatefulPublisher(1)
    dut = source | Cache(2)
    cb = mock.Mock()
    dut | Sink(cb)

    cb.assert_called_once_with(1)

    source.notify(1)
    cb.assert_called_once_with(1)

    cb.reset_mock()

    source.notify(2)
    cb.assert_called_once_with(2)

from unittest import mock
import pytest

from broqer import Disposable
from broqer.op import Sink, cache, Sink, Trace
from broqer.subject import Subject

@pytest.mark.parametrize('operator_cls', [Sink, Trace])
def test_sink(operator_cls):
    cb = mock.Mock()

    s = Subject()
    sink_instance = operator_cls(s, cb)
    assert isinstance(sink_instance, Disposable)

    assert not cb.called
    assert len(s.subscriptions) == 1

    # test various emits on source
    with pytest.raises(TypeError):
        s.emit()

    s.emit(None)
    cb.assert_called_with(None)

    s.emit(1)
    cb.assert_called_with(1)

    s.emit((1, 2))
    cb.assert_called_with((1, 2))

    # testing dispose()
    cb.reset_mock()

    sink_instance.dispose()
    assert len(s.subscriptions) == 0

    s.emit(1)
    assert not cb.called

@pytest.mark.parametrize('operator_cls', [Sink, Trace])
def test_sink(operator_cls):
    cb = mock.Mock()

    s = Subject()
    sink_instance = s | operator_cls(cb, unpack=True)
    assert isinstance(sink_instance, Disposable)

    # test various emits on source
    with pytest.raises(TypeError):
        s.emit()

    with pytest.raises(TypeError):
        s.emit(1)

    cb.assert_not_called()

    s.emit( (1, 2) )
    cb.assert_called_with(1,2)

@pytest.mark.parametrize('operator_cls', [Sink, Trace])
def test_sink_without_function(operator_cls):
    s = Subject()
    sink_instance = s | operator_cls()
    assert isinstance(sink_instance, Disposable)
    assert len(s.subscriptions) == 1

    s.emit(1)

@pytest.mark.parametrize('operator', [Sink, Trace])
def test_sink_on_subscription(operator):
    cb = mock.Mock()

    s = Subject()
    sink_instance = s | cache(0) | operator(cb)
    assert isinstance(sink_instance, Disposable)

    cb.assert_called_with(0)
    assert len(s.subscriptions) == 1

    s.emit(1)
    cb.assert_called_with(1)

    # testing dispose()
    cb.reset_mock()

    sink_instance.dispose()
    assert len(s.subscriptions) == 0

    s.emit(1)
    assert not cb.called


@pytest.mark.parametrize('operator_cls', [Sink, Trace])
def test_sink_partial(operator_cls):
    cb = mock.Mock()

    s = Subject()
    sink_instance = s | operator_cls(cb, 1, 2, 3, a=1)
    assert isinstance(sink_instance, Disposable)

    assert not cb.called
    assert len(s.subscriptions) == 1

    # test various emits on source
    s.emit(None)
    cb.assert_called_with(1, 2, 3, None, a=1)

    s.emit(1)
    cb.assert_called_with(1, 2, 3, 1, a=1)

    s.emit((1, 2))
    cb.assert_called_with(1, 2, 3, (1, 2), a=1)

    # testing dispose()
    cb.reset_mock()

    sink_instance.dispose()
    assert len(s.subscriptions) == 0

    s.emit(1)
    assert not cb.called

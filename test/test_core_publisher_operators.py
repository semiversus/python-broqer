from unittest import mock
import pytest

from broqer import Value, Publisher, op

def test_operator_with_publishers():
    v1 = Value(0)
    v2 = Value(0)

    o = v1 + v2

    assert isinstance(o, Publisher)
    assert o.get() == 0

    v1.emit(1)
    assert o.get() == 1

    assert len(o.subscriptions) == 0

    mock_sink = mock.Mock()

    o | op.sink(mock_sink)
    assert len(o.subscriptions) == 1
    mock_sink.assert_called_once_with(1)
    mock_sink.reset_mock()

    v2.emit(3)
    mock_sink.assert_called_once_with(4)

def test_operator_with_constant():
    v1 = Value(0)
    v2 = 1

    o = v1 + v2

    assert isinstance(o, Publisher)
    assert o.get() == 1

    v1.emit(1)
    assert o.get() == 2

    assert len(o.subscriptions) == 0

    mock_sink = mock.Mock()

    o | op.sink(mock_sink)
    assert len(o.subscriptions) == 1
    mock_sink.assert_called_once_with(2)
    mock_sink.reset_mock()

    v1.emit(3)
    mock_sink.assert_called_once_with(4)

def test_operator_with_constant_r():
    v1 = 1
    v2 = Value(0)

    o = v1 - v2

    assert isinstance(o, Publisher)
    assert o.get() == 1

    v2.emit(1)
    assert o.get() == 0

    assert len(o.subscriptions) == 0

    mock_sink = mock.Mock()

    o | op.sink(mock_sink)
    assert len(o.subscriptions) == 1
    mock_sink.assert_called_once_with(0)
    mock_sink.reset_mock()

    v2.emit(3)
    mock_sink.assert_called_once_with(-2)


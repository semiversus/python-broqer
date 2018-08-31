from unittest import mock
import pytest

from broqer import Value, Publisher, op
import operator

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

@pytest.mark.parametrize('operator, l_value, r_value, result', [
    (operator.lt, 0, 1, True),
    (operator.lt, 1, 0, False),
    (operator.lt, 1, 1, False),
])
def test_with_publisher(operator, l_value, r_value, result):
    vl = Value(l_value)
    vr = Value(r_value)
    pl = Publisher()
    pr = Publisher()
    cl = l_value
    cr = r_value

    o1 = operator(vl, vr)
    o2 = operator(vl, cr)
    o3 = operator(vl, pr)

    o4 = operator(pl, vr)
    o5 = operator(pl, cr)
    o6 = operator(pl, pr)

    o7 = operator(cl, vr)
    o8 = operator(cl, cr)
    o9 = operator(cl, pr)

    mock_sink_o3 = mock.Mock()
    mock_sink_o4 = mock.Mock()
    mock_sink_o5 = mock.Mock()
    mock_sink_o6 = mock.Mock()
    mock_sink_o9 = mock.Mock()

    o3 | op.sink(mock_sink_o3)
    o4 | op.sink(mock_sink_o4)
    o5 | op.sink(mock_sink_o5)
    o6 | op.sink(mock_sink_o6)
    o9 | op.sink(mock_sink_o9)

    for output in (o1, o2, o3, o4, o5, o6, o7, o9):
        assert isinstance(output, Publisher)

    assert o8 == result

    for output in (o1, o2, o7):
        assert output.get() == result

    for output in (o3, o4, o5, o6, o9):
        with pytest.raises(ValueError):
            output.get()

    mock_sink_o3.assert_not_called()
    mock_sink_o4.assert_not_called()
    mock_sink_o5.assert_not_called()
    mock_sink_o6.assert_not_called()
    mock_sink_o9.assert_not_called()

    pl.notify(l_value)

    mock_sink_o3.assert_not_called()
    mock_sink_o4.assert_called_once_with(result)
    mock_sink_o5.assert_called_once_with(result)
    mock_sink_o6.assert_not_called()
    mock_sink_o9.assert_not_called()

    pr.notify(r_value)

    mock_sink_o3.assert_called_once_with(result)
    mock_sink_o4.assert_called_once_with(result)
    mock_sink_o5.assert_called_once_with(result)
    mock_sink_o6.assert_called_once_with(result)
    mock_sink_o9.assert_called_once_with(result)

def test_wrong_comparision():
    p1 = Publisher()
    p2 = Publisher()

    with pytest.raises(NotImplementedError):
        assert p1 == p2

    with pytest.raises(NotImplementedError):
        if p1 == p2: pass

    with pytest.raises(NotImplementedError):
        if p1 != p2: pass

    with pytest.raises(NotImplementedError):
        assert p2 in (p1, p2)

    with pytest.raises(NotImplementedError):
        p1 in (p2, p2)

    with pytest.raises(NotImplementedError):
        assert p1 not in (p2, p2)

    l = [p1, p2]
    with pytest.raises(NotImplementedError):
        l.remove(p2)
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
    (operator.lt, 0, 1, True), (operator.lt, 1, 0, False), (operator.lt, 1, 1, False), (operator.lt, 1, 'foo', TypeError),
    (operator.le, 0, 1, True), (operator.le, 1, 0, False), (operator.le, 1, 1, True), (operator.le, 1, 'foo', TypeError),
    (operator.eq, 1, 0, False), (operator.eq, 1, 1, True), (operator.eq, 1, 'foo', False), (operator.eq, 'foo', 'foo', True),
    (operator.ne, 1, 0, True), (operator.ne, 1, 1, False), (operator.ne, 1, 'foo', True), (operator.ne, 'foo', 'foo', False),
    (operator.ge, 0, 1, False), (operator.ge, 1, 0, True), (operator.ge, 1, 1, True), (operator.ge, 1, 'foo', TypeError),
    (operator.gt, 0, 1, False), (operator.gt, 1, 0, True), (operator.gt, 1, 1, False), (operator.gt, 1, 'foo', TypeError),
    (operator.add, 0, 1, 1), (operator.add, 0, 1.1, 1.1), (operator.add, 'ab', 'cd', 'abcd'), (operator.add, 'ab', 1, TypeError),
    (operator.and_, 0, 0, 0), (operator.and_, 5, 1, 1), (operator.and_, 5, 4, 4), (operator.and_, 'ab', 1, TypeError),
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
    try:
        o8 = operator(cl, cr)
    except Exception as e:
        assert isinstance(e, result)
        o8 = result  # to pass the following test

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
        try:
            assert output.get() == result
        except Exception as e:
            assert isinstance(e, result)

    for output in (o3, o4, o5, o6, o9):
        with pytest.raises(ValueError):
            output.get()

    mock_sink_o3.assert_not_called()
    mock_sink_o4.assert_not_called()
    mock_sink_o5.assert_not_called()
    mock_sink_o6.assert_not_called()
    mock_sink_o9.assert_not_called()

    try:
        pl.notify(l_value)
    except Exception as e:
        assert isinstance(e, result)
    else:
        mock_sink_o3.assert_not_called()
        mock_sink_o4.assert_called_once_with(result)
        mock_sink_o5.assert_called_once_with(result)
        mock_sink_o6.assert_not_called()
        mock_sink_o9.assert_not_called()

    try:
        pr.notify(r_value)
    except Exception as e:
        assert isinstance(e, result)
    else:
        mock_sink_o3.assert_called_once_with(result)
        mock_sink_o4.assert_called_once_with(result)
        mock_sink_o5.assert_called_once_with(result)
        mock_sink_o6.assert_called_once_with(result)
        mock_sink_o9.assert_called_once_with(result)

def test_wrong_comparision():
    p1 = Publisher()
    p2 = Publisher()

    with pytest.raises(ValueError):
        assert p1 == p2

    with pytest.raises(ValueError):
        if p1 == p2: pass

    with pytest.raises(ValueError):
        if p1 != p2: pass

    with pytest.raises(ValueError):
        assert p2 in (p1, p2)

    with pytest.raises(ValueError):
        p1 in (p2, p2)

    with pytest.raises(ValueError):
        assert p1 not in (p2, p2)

    l = [p1, p2]
    with pytest.raises(ValueError):
        l.remove(p2)

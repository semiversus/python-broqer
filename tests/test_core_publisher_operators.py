from unittest import mock
import pytest

from broqer import Value, Publisher, Subscriber, Sink, op
import operator

def test_operator_with_publishers():
    v1 = Value(0)
    v2 = Value(0)

    o = v1 + v2

    assert isinstance(o, Publisher)
    assert isinstance(o, Subscriber)
    assert o.get() == 0

    v1.emit(1)
    assert o.get() == 1

    assert len(o.subscriptions) == 0

    mock_sink = mock.Mock()

    o.subscribe(Sink(mock_sink))
    assert len(o.subscriptions) == 1
    mock_sink.assert_called_once_with(1)
    mock_sink.reset_mock()

    v2.emit(3)
    mock_sink.assert_called_once_with(4)

    with pytest.raises(ValueError):
        o.emit(0, who=Publisher())

    with pytest.raises(ValueError):
        Value(1).subscribe(o)

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

    o.subscribe(Sink(mock_sink))
    assert len(o.subscriptions) == 1
    mock_sink.assert_called_once_with(2)
    mock_sink.reset_mock()

    v1.emit(3)
    mock_sink.assert_called_once_with(4)

    with pytest.raises(TypeError):
        Value(1) | o

    with pytest.raises(ValueError):
        o.emit(0, who=Publisher())

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

    o.subscribe(Sink(mock_sink))
    assert len(o.subscriptions) == 1
    mock_sink.assert_called_once_with(0)
    mock_sink.reset_mock()

    v2.emit(3)
    mock_sink.assert_called_once_with(-2)

    with pytest.raises(TypeError):
        Value(1) | o

    with pytest.raises(ValueError):
        o.emit(0, who=Publisher())

@pytest.mark.parametrize('operator, l_value, r_value, result', [
    (operator.lt, 0, 1, True), (operator.lt, 1, 0, False), (operator.lt, 1, 1, False), (operator.lt, 1, 'foo', TypeError),
    (operator.le, 0, 1, True), (operator.le, 1, 0, False), (operator.le, 1, 1, True), (operator.le, 1, 'foo', TypeError),
    (operator.eq, 1, 0, False), (operator.eq, 1, 1, True), (operator.eq, 1, 'foo', False), (operator.eq, 'foo', 'foo', True),
    (operator.ne, 1, 0, True), (operator.ne, 1, 1, False), (operator.ne, 1, 'foo', True), (operator.ne, 'foo', 'foo', False),
    (operator.ge, 0, 1, False), (operator.ge, 1, 0, True), (operator.ge, 1, 1, True), (operator.ge, 1, 'foo', TypeError),
    (operator.gt, 0, 1, False), (operator.gt, 1, 0, True), (operator.gt, 1, 1, False), (operator.gt, 1, 'foo', TypeError),
    (operator.add, 0, 1, 1), (operator.add, 0, 1.1, 1.1), (operator.add, 'ab', 'cd', 'abcd'), (operator.add, 'ab', 1, TypeError),
    (operator.and_, 0, 0, 0), (operator.and_, 5, 1, 1), (operator.and_, 5, 4, 4), (operator.and_, 'ab', 1, TypeError),
    (operator.lshift, 0, 0, 0), (operator.lshift, 5, 1, 10), (operator.lshift, 5, 4, 80), (operator.lshift, 'ab', 1, TypeError),
    (operator.mod, 0, 0, ZeroDivisionError), (operator.mod, 5, 1, 0), (operator.mod, 5, 4, 1), (operator.mod, 1, 'ab', TypeError),
    # str%tuple is tested seperatly
    (operator.mul, 0, 0, 0), (operator.mul, 5, 1, 5), (operator.mul, 'ab', 4, 'abababab'), (operator.mul, 1, 'ab', 'ab'), (operator.mul, (1,2), 'ab', TypeError),
    (operator.pow, 0, 0, 1), (operator.pow, 5, 2, 25), (operator.pow, 'ab', 4, TypeError),
    (operator.rshift, 0, 0, 0), (operator.rshift, 5, 1, 2), (operator.rshift, 5, 4, 0), (operator.rshift, 'ab', 1, TypeError),
    (operator.sub, 0, 0, 0), (operator.sub, 5, 1, 4), (operator.sub, 1, 4, -3), (operator.sub, 'ab', 1, TypeError),
    (operator.xor, 0, 0, 0), (operator.xor, 5, 1, 4), (operator.xor, 5, 3, 6), (operator.xor, 'ab', 1, TypeError),
    # concat is tested seperatly
    # getitem is tested seperatly
    (operator.floordiv, 0, 0, ZeroDivisionError), (operator.floordiv, 5, 4, 1), (operator.floordiv, 5, 'ab', TypeError),
    (operator.truediv, 0, 0, ZeroDivisionError), (operator.truediv, 5, 4, 1.25), (operator.truediv, 5, 'ab', TypeError),
])
def test_with_publisher(operator, l_value, r_value, result):
    vl = Value(l_value)
    vr = Value(r_value)
    cl = l_value
    cr = r_value

    o1 = operator(vl, vr)
    o2 = operator(vl, cr)
    o3 = operator(cl, vr)
    try:
        o4 = operator(cl, cr)
    except Exception as e:
        assert isinstance(e, result)
        o4 = result  # to pass the following test

    mock_sink_o3 = mock.Mock()

    try:
        o3.subscribe(Sink(mock_sink_o3))
    except Exception as e:
        assert isinstance(e, result)

    for output in (o1, o2, o3):
        assert isinstance(output, Publisher)

    assert o4 == result

    for output in (o1, o2, o3):
        try:
            assert output.get() == result
        except Exception as e:
            assert isinstance(e, result)

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

def test_mod_str():
    v1 = Publisher('%.2f %d')
    v2 = Value((0,0))

    o = v1%v2

    assert isinstance(o, Publisher)
    assert o.get() == '0.00 0'

    v2.emit((1,3))
    assert o.get() == '1.00 3'

def test_concat():
    v1 = Publisher((1,2))
    v2 = Value((0,0))

    o = v1+v2

    assert isinstance(o, Publisher)
    assert o.get() == (1,2,0,0)

    v2.emit((1,3))
    assert o.get() == (1,2,1,3)

def test_getitem():
    v1 = Value(('a','b','c'))
    v2 = Value(2)

    o = (v1[v2])

    assert isinstance(o, Publisher)
    assert o.get() == 'c'

    v2.emit(1)
    assert o.get() == 'b'

from collections import Counter
import math

@pytest.mark.parametrize('operator, value, result', [
    (operator.neg, -5, 5), (operator.neg, 'ab', TypeError), (operator.pos, -5, -5),
    (operator.pos, Counter({'a':0, 'b':1}), Counter({'b':1})), (operator.abs, -5, 5),
    (operator.invert, 5, -6), (round, 5.2, 5), (round, 5.8, 6), (math.trunc, -5.2, -5),
    (math.floor, -5.2, -6), (math.ceil, -5.2, -5),
    (op.Not, 5, False), (op.Not, 0, True), (op.Not, True, False),
    (op.Not, False, True),
    (op.Str, 123, '123'), (op.Str, (1, 2), '(1, 2)'), (op.Str, 1.23, '1.23'),
    (op.Bool, 0, False), (op.Bool, 1, True), (op.Bool, 'False', True), (op.Bool, (1,2,3), True),
    (op.Bool, {}, False), (op.Bool, None, False), (op.Bool, 513.17, True), (op.Bool, 0.0, False),
    (op.Int, 1.99, 1), (op.Int, '123', 123), (op.Int, (1, 2, 3), TypeError), (op.Int, None, TypeError),
    (op.Float, 1, 1.0), (op.Float, '12.34', 12.34), (op.Float, 'abc', ValueError),
    (op.Repr, 123, '123'), (op.Repr, 'abc', '\'abc\''), (op.Repr, int, '<class \'int\'>'),
    (op.Len, (), 0), (op.Len, [1,2,3], 3), (op.Len, 'abcde', 5), (op.Len, None, TypeError),
])
def test_unary_operators(operator, value, result):
    v = Publisher(value)

    try:
        value_applied = operator(v).get()
    except Exception as e:
        assert isinstance(e, result)
    else:
        assert value_applied == result

    cb = mock.Mock()

    try:
        operator(v).subscribe(Sink(cb))
    except Exception as e:
        assert isinstance(e, result)
    else:
        assert cb.mock_called_once_with(result)

    with pytest.raises(TypeError):
        Value(1) | operator(v)

    with pytest.raises(ValueError):
        operator(v).emit(0, who=Publisher())

def test_in_operator():
    pi = Value(1)
    ci = 1

    pc = Value((1,2,3))
    cc = (1, 2, 3)

    dut1 = op.In(pi, pc)
    dut2 = op.In(ci, pc)
    dut3 = op.In(pi, cc)
    with pytest.raises(TypeError):
        op.In(ci, cc)

    assert dut1.get() == True
    assert dut2.get() == True
    assert dut3.get() == True

    pi.emit('a')
    pc.emit((2.3, 'b'))

    assert dut1.get() == False
    assert dut2.get() == False
    assert dut3.get() == False

def test_getattr_method():
    p = Publisher('')
    p.inherit_type(str)

    dut1 = p.split()
    dut2 = p.split(',')
    dut3 = p.split(sep = '!')

    mock1 = mock.Mock()
    mock2 = mock.Mock()
    mock3 = mock.Mock()

    dut1.subscribe(Sink(mock1))
    dut2.subscribe(Sink(mock2))
    dut3.subscribe(Sink(mock3))

    assert dut1.get() == []
    assert dut2.get() == ['']
    assert dut3.get() == ['']

    mock1.assert_called_once_with([])
    mock2.assert_called_once_with([''])
    mock3.assert_called_once_with([''])

    mock1.reset_mock()
    mock2.reset_mock()
    mock3.reset_mock()

    p.notify('This is just a test, honestly!')

    assert dut1.get() == ['This', 'is', 'just', 'a', 'test,', 'honestly!']
    assert dut2.get() == ['This is just a test', ' honestly!']
    assert dut3.get() == ['This is just a test, honestly', '']

    mock1.assert_called_once_with(['This', 'is', 'just', 'a', 'test,', 'honestly!'])
    mock2.assert_called_once_with(['This is just a test', ' honestly!'])
    mock3.assert_called_once_with(['This is just a test, honestly', ''])

def test_inherit_getattr():
    p = Publisher('')
    p.inherit_type(str)

    dut = p.lower().split(' ')
    m = mock.Mock()
    dut.subscribe(Sink(m))
    m.assert_called_once_with([''])
    m.reset_mock()

    p.notify('This is a TEST')
    m.assert_called_once_with(['this', 'is', 'a', 'test'])

def test_inherit_with_operators():
    p = Publisher('')
    p.inherit_type(str)

    dut = op.Len(('abc' + p + 'ghi').upper())
    m = mock.Mock()
    dut.subscribe(Sink(m))
    m.assert_called_once_with(6)
    m.reset_mock()

    p.notify('def')
    m.assert_called_once_with(9)

def test_getattr_attribute():
    class Foo:
        a = None

        def __init__(self, a=5):
            self.a = a

    p = Publisher(Foo(3))
    p.inherit_type(Foo)

    dut = p.a
    m = mock.Mock()
    dut.subscribe(Sink(m))

    m.assert_called_once_with(3)
    assert dut.get() == 3
    m.reset_mock()

    p.notify(Foo(4))

    assert dut.get() == 4

    m.assert_called_once_with(4)

    with pytest.raises(ValueError):
        dut.emit(0, who=Publisher())

    with pytest.raises(AttributeError):
        dut.assnign(5)


def test_getattr_without_inherit():
    p = Publisher()

    class Foo:
        a = None

        def __init__(self, a=5):
            self.a = a

    with pytest.raises(AttributeError):
        dut = p.a

    with pytest.raises(AttributeError):
        p.assnign(5)

@pytest.mark.parametrize('operator, values, result', [
    (op.All, (False, False, False), False),
    (op.All, (False, True, False), False),
    (op.All, (True, True, True), True),
    (op.Any, (False, False, False), False),
    (op.Any, (False, True, False), True),
    (op.Any, (True, True, True), True),
    (op.BitwiseAnd, (0, 5, 15), 0),
    (op.BitwiseAnd, (7, 14, 255), 6),
    (op.BitwiseAnd, (3,), 3),
    (op.BitwiseOr, (0, 5, 8), 13),
    (op.BitwiseOr, (7, 14, 255), 255),
    (op.BitwiseOr, (3,), 3),
])
def test_multi_operators(operator, values, result):
    sources = [Publisher(v) for v in values]
    dut = operator(*sources)
    assert dut.get() == result

from unittest import mock
import pytest

from broqer import Disposable, Publisher, Value, Sink, Trace, build_sink, \
                   build_sink_factory


@pytest.mark.parametrize('operator_cls', [Sink, Trace])
def test_sink(operator_cls):
    cb = mock.Mock()

    s = Value()
    sink_instance = s.subscribe(operator_cls(cb))
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

    # testing dispose()s
    cb.reset_mock()

    sink_instance.dispose()
    assert len(s.subscriptions) == 0

    s.emit(1)
    assert not cb.called


@pytest.mark.parametrize('operator_cls', [Sink, Trace])
def test_sink2(operator_cls):
    cb = mock.Mock()

    s = Value()
    sink_instance = s.subscribe(operator_cls(cb, unpack=True))
    assert isinstance(sink_instance, Disposable)

    # test various emits on source
    with pytest.raises(TypeError):
        s.emit()

    with pytest.raises(TypeError):
        s.emit(1)

    cb.assert_not_called()

    s.emit((1, 2))
    cb.assert_called_with(1, 2)


@pytest.mark.parametrize('operator_cls', [Sink, Trace])
def test_sink_without_function(operator_cls):
    s = Value()
    sink_instance = s.subscribe(operator_cls())
    assert isinstance(sink_instance, Disposable)
    assert len(s.subscriptions) == 1

    s.emit(1)


@pytest.mark.parametrize('operator', [Sink, Trace])
def test_sink_on_subscription(operator):
    cb = mock.Mock()

    s = Value(0)
    sink_instance = s.subscribe(operator(cb))
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

    s = Value()
    sink_instance = s.subscribe(operator_cls(cb, 1, 2, 3, a=1))
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


@pytest.mark.parametrize(
    'build_kwargs, init_args, init_kwargs, ref_args, ref_kwargs, exception',
    [(None, (), {}, (), {}, None),
     ({'unpack': True}, (), {}, (), {'unpack': True}, None),
     ({'unpack': False}, (), {}, (), {'unpack': False}, None),
     ({'unpack': False}, (), {'unpack': False}, (), {'unpack': False},
      TypeError),
     (None, (1,), {'a': 2}, (1,), {'unpack': False, 'a': 2}, None),
     ({'unpack': True}, (1,), {'a': 2}, (1,), {'unpack': True, 'a': 2}, None),
     ({'unpack': False}, (1,), {'a': 2}, (1,), {'unpack': False, 'a': 2},
      None),
     ({'foo': 1}, (), {}, (), {}, TypeError),
     ])
def test_build(build_kwargs, init_args, init_kwargs, ref_args, ref_kwargs,
               exception):
    mock_cb = mock.Mock()
    ref_mock_cb = mock.Mock()

    reference = Sink(ref_mock_cb, *ref_args, **ref_kwargs)

    try:
        if build_kwargs is None:
            dut = build_sink_factory(mock_cb)(*init_args, **init_kwargs)
        else:
            dut = build_sink_factory(**build_kwargs)(mock_cb)(*init_args,
                                                      **init_kwargs)
    except Exception as e:
        assert isinstance(e, exception)
        return
    else:
        assert exception is None

    assert dut._unpack == reference._unpack

    v = Publisher((1, 2))
    v.subscribe(dut)
    v.subscribe(reference)

    assert mock_cb.mock_calls == ref_mock_cb.mock_calls
    assert len(mock_cb.mock_calls) == 1

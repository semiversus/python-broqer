from broqer import Publisher, Value
from broqer.op import Accumulate, Cache, CatchException, CombineLatest, Distinct, Sink

from unittest.mock import Mock
import pytest


@pytest.mark.parametrize('operator,args,kwargs,input,output', [
    (Accumulate, (), {'func':lambda a,b:(a+b,a+b), 'init':0}, (0, 1, 2, 3), (0, 1, 3, 6)),
    (Accumulate, (), {'func':lambda a,b:(a+b,a), 'init':0}, (0, 1, 2, 3), (0, 0, 1, 3)),
    (Accumulate, (lambda a,b:(a+b,a+b),), {'init':0}, (0, 1, 2, 3), (0, 1, 3, 6)),
    (Accumulate, (lambda a,b:(a+b,a+b), 0), {}, (0, 1, 2, 3), (0, 1, 3, 6)),
    (Cache, (0,), {}, (1, 2, 3), (0, 1, 2, 3)),
    (Cache, (0,1,2), {}, (1, 2, 3), ((0, 1, 2), 1, 2, 3)),
    (Cache, ('start',), {}, ('set', 'go'), ('start', 'set', 'go')),
    (Cache, (Exception,), {}, ('set', 1, (1,2), Value, None), (Exception, 'set', 1, (1,2), Value, None)),
    (Cache, (0,), {}, (1, 2, 3), (0, 1, 2, 3)),
    (CatchException, (Exception,), {}, (0, 1, 2), (0, 1, 2)),
    (CombineLatest, (Value('a'),), {}, (0, 1, 2), ((0, 'a'), (1, 'a'), (2, 'a'))),
    (CombineLatest, (), {}, (0, 1, 2), (0, 1, 2)),
    (CombineLatest, (Value(1),), {'map':lambda a,b:a+b}, (0, 1, 2), (1, 2, 3)),
    (CombineLatest, (Publisher(),), {'map':lambda a,b:a+b}, (0, 1, 2), ()),
])
def test_with_publisher(operator, args, kwargs, input, output):
    source = Publisher()
    sink = operator(source, *args, **kwargs)

    result = list()
    def _append(*args):
        if len(args) == 1:
            args = args[0]
        result.append(args)
    Sink(sink, _append)

    for v in input:
        if not isinstance(v, tuple):
            v = (v,)
        source.notify(*v)

    assert tuple(output) == tuple(result)

class _None:
    pass

@pytest.mark.parametrize('operator,args,kwargs,input,output', [
    # output is a tuple of three values:
    # 1. output of subscription to a non-stateful publisher
    # 2. output of subscription to a non-stateful publisher after emitting `input`
    # 3. output of subscription of a second subscriber after emitting `input`
    # 4. output of subscription to a stateful publisher with state input
    (Cache, (0,), {}, 1, (0, 1, 1, 1)),
    (CombineLatest, (), {}, 1, (_None, 1, 1, 1)),
    (CombineLatest, (Value(0),), {}, 1, (_None, (1, 0), (1, 0), (1, 0))),
    (CombineLatest, (Publisher(),), {}, 1, (_None, _None, _None, _None)),
    (CombineLatest, (), {'map':lambda v:v+1}, 1, (_None, 2, 2, 2)),
    (CombineLatest, (Value(1),), {'map':lambda a,b:a+b}, 2, (_None, 3, 3, 3)),
])
def test_on_subscription(operator, args, kwargs, input, output):
    if not isinstance(input, tuple):
        input = (input,)
    output = list(output)
    for i in range(4):
        if not isinstance(output[i], tuple) and output[i] != _None:
            output[i] = (output[i],)

    ### non-stateful publisher
    source = Publisher()
    sink = operator(source, *args, **kwargs)
    mock = Mock()
    Sink(sink, mock)

    if output[0] == _None:
        mock.assert_not_called()
    else:
        mock.assert_called_with(*output[0])

    mock.reset_mock()

    source.notify(*input)

    if output[1] == _None:
        mock.assert_not_called()
    else:
        mock.assert_called_with(*output[1])

    # second subscription after emit
    mock.reset_mock()
    Sink(sink, mock)

    if output[2] == _None:
        mock.assert_not_called()
    else:
        mock.assert_called_with(*output[2])

    ### with two subscriptions at start
    source = Publisher()
    sink = operator(source, *args, **kwargs)
    mock = Mock()
    d1 = Sink(sink, mock) # already tested
    Sink(sink, mock) # 2nd subscriber

    if output[0] == _None:
        mock.assert_not_called()
    else:
        mock.assert_called_with(*output[0])

    d1.dispose()

    source.notify(*input)

    if output[1] == _None:
        mock.assert_not_called()
    else:
        mock.assert_called_with(*output[1])

    ### stateful publisher
    source = Value(*input)
    sink = operator(source, *args, **kwargs)
    mock = Mock()
    Sink(sink, mock)

    if output[3] == _None:
        mock.assert_not_called()
    else:
        mock.assert_called_with(*output[3])

    mock.reset_mock()

    Sink(sink, mock) # 2nd subscription

    if output[3] == _None:
        mock.assert_not_called()
    else:
        mock.assert_called_with(*output[3])

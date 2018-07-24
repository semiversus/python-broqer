from broqer import Publisher, Value
from broqer.op import Accumulate, Cache, CatchException, CombineLatest, Sink

from unittest.mock import Mock
import pytest


@pytest.mark.parametrize('operator,args,kwargs,input,output', [
    (Cache, (0,), {}, (1, 2, 3), (0, 1, 2, 3)),
    (Cache, (0,1,2), {}, (1, 2, 3), ((0, 1, 2), 1, 2, 3)),
    (Cache, ('start',), {}, ('set', 'go'), ('start', 'set', 'go')),
    (Cache, (Exception,), {}, ('set', 1, (1,2), Value, None), (Exception, 'set', 1, (1,2), Value, None)),
    (Cache, (0,), {}, (1, 2, 3), (0, 1, 2, 3)),
    (CatchException, (Exception,), {}, (0, 1, 2), (0, 1, 2)),
    (CombineLatest, (Value('a'),), {}, (0, 1, 2), ((0, 'a'), (1, 'a'), (2, 'a'))),
    (CombineLatest, (), {}, (0, 1, 2), (0, 1, 2)),
    (CombineLatest, (Value(1),), {'map_':lambda a,b:a+b}, (0, 1, 2), (1, 2, 3)),
    (CombineLatest, (Publisher(),), {'map_':lambda a,b:a+b}, (0, 1, 2), ()),
])
def test_with_publisher(operator, args, kwargs, input, output):
    source = Publisher()
    sink = operator(source, *args, **kwargs)

    result = list()
    def _append(*args):
        result.append(unpack_args(*args))
    Sink(sink, _append)

    for v in input:
        if not isinstance(v, tuple):
            v = (v,)
        source.notify(*v)

    assert tuple(output) == tuple(result)

class _None:
    pass

@pytest.mark.parametrize('operator,args,kwargs,input,output', [
    # output is a tuple of five values:
    # 1. output of subscription to a non-stateful publisher
    # 2. output of subscription to a non-stateful publisher after emitting `input`
    # 3. output of subscription of a second subscriber after emitting `input`
    # 4. output of subscription after disposing all other subscriptions and re-subscribing
    # 5. output of subscription to a stateful publisher with state input
    (Cache, (0,), {}, 1, (0, 1, 1, 1, 1)),
    (CombineLatest, (), {}, 1, (_None, 1, 1, _None, 1)),
    (CombineLatest, (Value(0),), {}, 1, (_None, (1, 0), (1, 0), _None, (1, 0))),
    (CombineLatest, (Publisher(),), {}, 1, (_None, _None, _None, _None, _None)),
    (CombineLatest, (), {'map_':lambda v:v+1}, 1, (_None, 2, 2, _None, 2)),
    (CombineLatest, (Value(1),), {'map_':lambda a,b:a+b}, 2, (_None, 3, 3, _None, 3)),
])
def test_on_subscription(operator, args, kwargs, input, output):
    if not isinstance(input, tuple):
        input = (input,)
    output = list(output)
    for i in range(5):
        if not isinstance(output[i], tuple) and output[i] != _None:
            output[i] = (output[i],)

    ### non-stateful publisher
    source = Publisher()
    sink = operator(source, *args, **kwargs)
    mock1 = Mock()
    Sink(sink, mock1)

    if output[0] == _None:
        mock1.assert_not_called()
    else:
        mock1.assert_called_once_with(*output[0])

    mock1.reset_mock()

    source.notify(*input)

    if output[1] == _None:
        mock1.assert_not_called()
    else:
        mock1.assert_called_once_with(*output[1])

    # second subscription after emit
    mock1.reset_mock()
    mock2 = Mock()
    Sink(sink, mock2)

    if output[2] == _None:
        mock2.assert_not_called()
    else:
        mock2.assert_called_once_with(*output[2])

    ### with two subscriptions at start
    source = Publisher()
    sink = operator(source, *args, **kwargs)
    mock1 = Mock()
    mock2 = Mock()
    d1 = Sink(sink, mock1) # already tested
    d2 = Sink(sink, mock2) # 2nd subscriber

    if output[0] == _None:
        mock1.assert_not_called()
        mock2.assert_not_called()
    else:
        mock1.assert_called_once_with(*output[0])
        mock2.assert_called_once_with(*output[0])

    d1.dispose()
    mock1.reset_mock()
    mock2.reset_mock()

    source.notify(*input)

    mock1.assert_not_called()

    if output[1] == _None:
        mock2.assert_not_called()
    else:
        mock2.assert_called_once_with(*output[1])

    d2.dispose()
    mock3 = Mock()
    Sink(sink, mock3) # already tested

    if output[3] == _None:
        mock3.assert_not_called()
    else:
        mock3.assert_called_once_with(*output[3])

    ### stateful publisher
    source = Value(*input)
    sink = operator(source, *args, **kwargs)
    mock1 = Mock()
    Sink(sink, mock1)

    if output[4] == _None:
        mock1.assert_not_called()
    else:
        mock1.assert_called_once_with(*output[4])

    mock1.reset_mock()

    mock2 = Mock()
    Sink(sink, mock2) # 2nd subscription

    mock1.assert_not_called()

    if output[4] == _None:
        mock2.assert_not_called()
    else:
        mock2.assert_called_once_with(*output[4])

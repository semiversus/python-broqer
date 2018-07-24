import pytest

from broqer import Publisher
from broqer.op import Accumulate

from .helper import check_single_operator, Collector

def min_max_avg(state, input):
    """emit minimum, maximum and average. Keep internal state with minimum,
    maximum, sum and count of emits"""
    _min, _max, _sum, _count = state
    _min = min(_min, input)
    _max = max(_max, input)
    _sum = sum((_sum, input))
    _count += 1
    return (_min, _max, _sum, _count), (_min, _max, _sum/_count)

def distinct_elements(state, input):
    """count how many distinct elements had been emitted yet"""
    state = set(state)
    state.add(input)
    return state, len(state)

@pytest.mark.parametrize('args, kwargs, input_vector, output_vector', [
    ((), {'func':lambda a,b:(a+b,a+b), 'init':0}, (0, 1, 2, 3), (0, 1, 3, 6)),
    ((), {'func':lambda a,b:(a+b,a), 'init':0}, (0, 1, 2, 3), (0, 0, 1, 3)),
    ((lambda a,b:(a+b,a+b),), {'init':0}, (0, 1, 2, 3), (0, 1, 3, 6)),
    ((lambda a,b:(a+b,a+b), 0), {}, (0, 1, 2, 3), (0, 1, 3, 6)),
    ((min_max_avg, (0, 0, 0, 0)), {}, (0, 2, 1, -1, -2, 0, 3), ((0, 0, 0), (0, 2, 1), (0, 2, 1), (-1, 2, 0.5), (-2, 2, 0), (-2, 2, 0), (-2, 3, 3/7))),
    ((distinct_elements, ()), {}, (0, 1, 1, 2, 0, 2), (1, 2, 2, 3, 3, 3)),
    ((distinct_elements, (2,3)), {}, (0, 1, 1, 2, 0, 2), (3, 4, 4, 4, 4, 4)),
])
def test_with_publisher(args, kwargs, input_vector, output_vector):
    check_single_operator(Accumulate, args, kwargs, input_vector, output_vector, has_state=True)

def test_reset():
    source = Publisher()
    dut = Accumulate(source, distinct_elements, init=())

    collector = Collector()
    dut.subscribe(collector)

    source.notify(1)
    source.notify(2)
    source.notify(0)
    source.notify(1)
    assert collector.result_vector == (1, 2, 3, 3)

    collector.reset()
    dut.reset((1, 3))
    source.notify(1)
    source.notify(2)
    assert collector.result_vector == (2, 3)

import pytest

from broqer.op import CombineLatest, Just, sink
from broqer import Publisher, StatefulPublisher, UNINITIALIZED

from .helper import check_multi_operator, NONE, Collector

@pytest.mark.parametrize('kwargs, input_vector, output_vector', [
    ({}, ((1,2), (NONE,3), (2,NONE), (2,3)), ((1,2),(1,3),(2,3),NONE)),
    ({}, ((1,), (2,), (2,), (3,)), (( (1,), (2,), NONE, (3,)))),
    ({}, ((1,NONE,NONE,NONE), (NONE,2,NONE,NONE), (NONE,3,NONE,NONE), (NONE,NONE,4,5)), ((NONE,NONE,NONE,(1,3,4,5)))),
    ({'map_':lambda a,b:a+b}, ((1,1), (NONE, 2), (1, NONE), (NONE, -5)), (2, 3, NONE, -4)),
    ({'map_':lambda a,b:a>b}, ((1,1), (NONE, 2), (1, NONE), (NONE, -5)), (False, NONE, NONE, True)),
])
def test_with_publisher(kwargs, input_vector, output_vector):
    check_multi_operator(CombineLatest, kwargs, input_vector, output_vector, has_state=True)

def test_emit_on():
    source = Publisher()
    source2 = Publisher()
    dut = CombineLatest(source, source2, emit_on=source2)
    dut2 = CombineLatest(source, source2, emit_on=(source, source2))
    dut3 = CombineLatest(source, source2, emit_on=source, map_=lambda a,b:a+b)

    collector = Collector()
    collector2 = Collector()
    collector3 = Collector()
    dut.subscribe(collector)
    dut2.subscribe(collector2)
    dut3.subscribe(collector3)

    source2.notify(1)
    source.notify(2)
    source2.notify(0)
    source.notify(1)
    assert collector.result_vector == ((2,0),)
    assert collector2.result_vector == ((2,1), (2,0), (1,0))
    assert collector3.result_vector == (3, 1)

def test_allow_stateless():
    source1 = StatefulPublisher(0)
    source2 = Publisher()

    dut = CombineLatest(source1, source2, allow_stateless=True)
    assert dut.get() == (0, UNINITIALIZED)

    collector = Collector()
    dut.subscribe(collector)

    assert dut.get() == (0, UNINITIALIZED)
    assert collector.result_vector == ((0, UNINITIALIZED),)

    source1.notify(1)
    source2.notify(True)
    source1.notify(2)
    source2.notify(False)

    assert collector.result_vector == ((0, UNINITIALIZED), (1, UNINITIALIZED),
        (1, True), (2, UNINITIALIZED), (2, False))

def test_allow_stateless_extensive():
    source1 = StatefulPublisher(0)
    source2 = Publisher()
    source3 = StatefulPublisher(0)
    source4 = Publisher()

    dut = CombineLatest(source1, source2, source3, source4,
        allow_stateless=True, emit_on=(source2, source3))

    with pytest.raises(ValueError):
        dut | sink()  # source4 is stateless but not in emit_on list

    def reverse(s1, s2, s3, s4):
        return (s4, s3, s2, s1)

    dut = CombineLatest(source1, source2, source3, source4, map_=reverse,
        allow_stateless=True, emit_on=(source2, source3, source4))

    assert dut.get() == (UNINITIALIZED, 0, UNINITIALIZED, 0)

    collector = Collector()
    dut.subscribe(collector)

    assert dut.get() == (UNINITIALIZED, 0, UNINITIALIZED, 0)
    assert collector.result_vector == ((UNINITIALIZED, 0, UNINITIALIZED, 0),)

    collector.reset()
    source1.notify(1)
    source2.notify(2)
    assert dut.get() == (UNINITIALIZED, 0, UNINITIALIZED, 1)
    assert collector.result_vector == ((UNINITIALIZED, 0, 2, 1),)

    collector.reset()
    source3.notify(3)
    source4.notify(4)
    assert dut.get() == (UNINITIALIZED, 3, UNINITIALIZED, 1)
    assert collector.result_vector == ((UNINITIALIZED, 3, UNINITIALIZED, 1), (4, 3, UNINITIALIZED, 1),)
import pytest

from broqer.op import CombineLatest, Just, sink
from broqer import Publisher, StatefulPublisher, Subject, UNINITIALIZED

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
    with pytest.raises(ValueError):
        dut.get()

    collector = Collector()
    disposable = dut.subscribe(collector)

    with pytest.raises(ValueError):
        dut.get()
    assert collector.result_vector == ()

    source1.notify(1)
    source2.notify(True)
    source1.notify(2)
    source2.notify(False)

    assert collector.result_vector == ((1, UNINITIALIZED),
        (1, True), (2, UNINITIALIZED), (2, False))

    # combine latest should also emit when stateless publisher is emitting
    collector.reset()

    source2.notify(False)
    assert collector.result_vector == ((2, False),)

    source2.notify(False)
    assert collector.result_vector == ((2, False), (2, False))

    source1.notify(0)
    assert collector.result_vector == ((2, False), (2, False), (0, UNINITIALIZED))

    disposable.dispose()
    assert len(dut.subscriptions) == 0

    source3 = StatefulPublisher(0)
    dut2 = CombineLatest(dut, source3)

    with pytest.raises(ValueError):
        dut2.get()

def test_stateless_nested():
    source1 = Publisher()
    dut1 = CombineLatest(source1, allow_stateless=True)

    source2 = Publisher()
    dut2= CombineLatest(dut1, source2, allow_stateless=True)

    assert len(source1.subscriptions) == 0
    assert len(source2.subscriptions) == 0
    assert len(dut1.subscriptions) == 0
    assert len(dut2.subscriptions) == 0

    collector = Collector()
    dut2 | collector
    assert len(source1.subscriptions) == 1
    assert len(source2.subscriptions) == 1
    assert len(dut1.subscriptions) == 1
    assert len(dut2.subscriptions) == 1

    with pytest.raises(ValueError):
        dut2.get()

    assert collector.result_vector == ()

    collector.reset()
    source1.notify(True)
    assert collector.result_vector == (((True,),UNINITIALIZED),)

    collector.reset()
    source2.notify(False)

    assert collector.result_vector == ((UNINITIALIZED,False),)

def test_stateless_only():
    source1 = Publisher()
    source2 = Publisher()

    dut = CombineLatest(source1, source2, allow_stateless=True)

    collector = Collector()
    dut.subscribe(collector)

    with pytest.raises(ValueError):
        dut.get()

    source1.notify(1)
    source2.notify(True)
    source1.notify(2)
    source2.notify(False)

    assert collector.result_vector == ((1, UNINITIALIZED),
        (UNINITIALIZED, True), (2, UNINITIALIZED),
        (UNINITIALIZED, False))

    # special case with one source
    dut2 = CombineLatest(source1, allow_stateless=True)
    collector2 = Collector()
    dut2.subscribe(collector2)

    with pytest.raises(ValueError):
        dut2.get()

    assert collector2.result_vector == ()

def test_stateless_map():
    source1 = StatefulPublisher(0)
    source2 = Publisher()

    dut = CombineLatest(source1, source2, map_=lambda a,b: a+(0 if b is UNINITIALIZED else b), allow_stateless=True)

    collector = Collector()
    dut.subscribe(collector)

    with pytest.raises(ValueError):
        dut.get()
    assert collector.result_vector == ()

    collector.reset()
    source1.notify(1)
    assert collector.result_vector == (1,)

    source1.notify(1)
    assert collector.result_vector == (1,)

    source1.notify(1.0)
    assert collector.result_vector == (1,)

    source2.notify(0)
    assert collector.result_vector == (1, 1)

    source2.notify(1)
    assert collector.result_vector == (1, 1, 2)

    source2.notify(1)
    assert collector.result_vector == (1, 1, 2, 2)

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

    with pytest.raises(ValueError):
        dut.get()

    collector = Collector()
    dut.subscribe(collector)

    with pytest.raises(ValueError):
        dut.get()
    assert collector.result_vector == ()

    collector.reset()
    source1.notify(1)
    source2.notify(2)
    with pytest.raises(ValueError):
        dut.get()
    assert collector.result_vector == ((UNINITIALIZED, 0, 2, 1),)

    collector.reset()
    source3.notify(3)
    source4.notify(4)
    with pytest.raises(ValueError):
        dut.get()
    assert collector.result_vector == ((UNINITIALIZED, 3, UNINITIALIZED, 1), (4, 3, UNINITIALIZED, 1),)
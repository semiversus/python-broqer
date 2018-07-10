from typing import Any

from broqer import Subscriber, Publisher, unpack_args, SubscriptionDisposable, to_args

class Collector(Subscriber):
    def __init__(self):
        Subscriber.__init__(self)
        self._state_vector = []

    def emit(self, *args: Any, who: Publisher) -> None:
        self._state_vector.append(unpack_args(*args))

    @property
    def state_vector(self):
        return tuple(self._state_vector)

    def reset(self):
        """clear the state_vector"""
        self._state_vector.clear()

    def __len__(self):
        return len(self._state_vector)

    @property
    def state(self):
        """returns the last state in state_vector"""
        return self._state_vector[-1]


class NONE:
    pass


class InitializedPublisher(Publisher):
    def __init__(self, *init):
        Publisher.__init__(self)
        self._state = init

    def subscribe(self, subscriber: 'Subscriber') -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber)
        if unpack_args(*self._state) != NONE :
            print('EMIT', self._state)
            subscriber.emit(*self._state, who=self)
        return disposable

    def get(self):
        return self._state if unpack_args(*self._state) != NONE else None

    def notify(self, *args: Any) -> None:
        self._state = args
        Publisher.notify(self, *args)

def check_single_operator(cls, args, kwargs, input_vector, output_vector, initial_state=None, has_state=False):
    check_operator(cls, args, kwargs, input_vector, output_vector, initial_state, has_state, multi=False)

def check_multi_operator(cls, kwargs, input_vector, output_vector, initial_state=None, has_state=False):
    check_operator(cls, (), kwargs, input_vector, output_vector, initial_state, has_state, multi=True)

def check_operator(cls, args, kwargs, input_vector, output_vector, initial_state=None, has_state=False, multi=False):
    # Test with Publisher
    if multi:
        sources = tuple(Publisher() for _ in input_vector[0])
    else:
        input_vector = tuple((v,) for v in input_vector)
        sources = (Publisher(),)
    dut = cls(*sources, *args, **kwargs)

    collector = Collector()
    collector2 = Collector()

    assert dut.get() == initial_state
    assert all(len(source) == 0 for source in sources)
    assert len(dut) == 0

    dispose_collector = dut.subscribe(collector)
    assert len(dut) == 1
    assert all(len(source) == 1 for source in sources)

    if not initial_state:
        assert not collector.state_vector
    else:
        assert to_args(collector.state) == initial_state

    with dut.subscribe(collector2):
        assert len(dut) == 2
        assert all(len(source) == 1 for source in sources)
        if initial_state is None:
            assert not collector.state_vector
        else:
            assert to_args(collector.state) == initial_state

    assert dut.get() == initial_state

    initialized = not (initial_state is None)
    for v_emits, v_result in zip(input_vector, output_vector):
        print(v_emits, v_result)
        collector_len = len(collector)
        collector2_len = len(collector2)
        for source, v_emit in zip(sources, v_emits):
            if v_emit is not NONE:
                source.notify(*to_args(v_emit))
        print(collector.state_vector)
        with dut.subscribe(collector2):
            pass
        if v_result is not NONE:
            initialized = True
        if v_result is NONE:
            assert collector_len == len(collector)
            if initialized:
                assert collector2_len + 1 == len(collector2)
            else:
                assert collector2_len == len(collector2)
                assert collector2_len == 0
                assert collector_len == 0
        elif has_state:
            assert collector_len + 1 == len(collector)
            assert collector2_len + 1 == len(collector2)
            assert unpack_args(*dut.get()) == collector.state
            assert collector2.state == v_result
            assert collector.state == v_result
        else:
            assert collector_len + 1 == len(collector)
            assert collector2_len == len(collector2)
            assert dut.get() is None
            assert collector.state == v_result

    # Dispose collector
    dispose_collector.dispose()

    assert all(len(source) == 0 for source in sources)
    if has_state:
        assert unpack_args(*dut.get()) == collector.state
    else:
        assert dut.get() is None

    # Test with InitializedPublisher
    sources = tuple(InitializedPublisher(*to_args(v)) for v in input_vector[0])
    dut = cls(*sources, *args, **kwargs)

    collector = Collector()
    collector2 = Collector()

    get_result = dut.get()

    dut.subscribe(collector)

    if output_vector[0] == NONE:
        _cmp_value = unpack_args(*initial_state) if initial_state is not None else None
    else:
        _cmp_value = output_vector[0]

    if NONE in input_vector[0]:
        assert len(collector) == 0
        assert get_result == None
        assert dut.get() == None
        with dut.subscribe(collector2):
            pass
        assert len(collector2) == 0
    else:
        assert len(collector) == 1
        assert collector.state == _cmp_value
        assert unpack_args(*get_result) == _cmp_value
        assert unpack_args(*dut.get()) == _cmp_value
        with dut.subscribe(collector2):
            assert collector2.state == _cmp_value

    initialized = NONE not in input_vector[0]
    for v_emits, v_result in zip(input_vector[1:], output_vector[1:]):
        collector_len = len(collector)
        collector2_len = len(collector2)
        for source, v_emit in zip(sources, v_emits):
            if v_emit is not NONE:
                source.notify(*to_args(v_emit))
        if v_result is not NONE:
            initialized = True
        if initialized:
            assert unpack_args(*dut.get()) == collector.state
            with dut.subscribe(collector2):
                assert collector2.state == collector.state
            assert collector2_len + 1 == len(collector2)
        else:
            assert dut.get() == None
            assert collector2_len == len(collector2)
        if v_result is NONE:
            assert collector_len == len(collector)
        else:
            assert collector_len + 1 == len(collector)
            assert v_result == collector.state
            assert v_result == collector2.state

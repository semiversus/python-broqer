import asyncio
from typing import Any

from broqer import Subscriber, Publisher, unpack_args, SubscriptionDisposable, to_args

class Collector(Subscriber):
    def __init__(self, loop=None):
        Subscriber.__init__(self)
        self._state_vector = []
        if loop is not None:
            self._timestamp_vector = []
            self._start_timestamp = loop.time()
        self._loop = loop

    def emit(self, *args: Any, who: Publisher) -> None:
        self._state_vector.append(unpack_args(*args))
        if self._loop is not None:
            self._timestamp_vector.append(self._loop.time() - self._start_timestamp)

    @property
    def state_vector(self):
        return tuple(self._state_vector)

    @property
    def timestamp_vector(self):
        return tuple(self._timestamp_vector)

    def reset(self):
        """clear the state_vector"""
        self._state_vector.clear()
        if self._loop is not None:
            self._timestamp_vector.clear()
            self._start_timestamp = self._loop.time()

    def __len__(self):
        return len(self._state_vector)

    @property
    def state(self):
        """returns the last state in state_vector"""
        return self._state_vector[-1]

    @property
    def timestamp(self):
        return self._timestamp_vector[-1]


class NONE:
    pass


class InitializedPublisher(Publisher):
    def __init__(self, *init):
        Publisher.__init__(self)
        self._state = init

    def subscribe(self, subscriber: 'Subscriber') -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber)
        if unpack_args(*self._state) != NONE :
            subscriber.emit(*self._state, who=self)
        return disposable

    def get(self):
        return self._state if unpack_args(*self._state) != NONE else None

    def reset(self, *init):
        self._state = init

    def notify(self, *args: Any) -> None:
        self._state = args
        Publisher.notify(self, *args)

def check_single_operator(cls, args, kwargs, input_vector, output_vector, initial_state=None, has_state=False):
    input_vector = tuple((v,) for v in input_vector)
    check_operator(cls, args, kwargs, input_vector, output_vector, initial_state, has_state, stateful=False)
    check_operator(cls, args, kwargs, input_vector, output_vector, initial_state, has_state, stateful=True)

def check_multi_operator(cls, kwargs, input_vector, output_vector, initial_state=None, has_state=False):
    check_operator(cls, (), kwargs, input_vector, output_vector, initial_state, has_state, stateful=False)
    check_operator(cls, (), kwargs, input_vector, output_vector, initial_state, has_state, stateful=True)

def check_operator(cls, args, kwargs, input_vector, output_vector, initial_state=None, has_state=False, stateful=False):
    # setup
    first_input = input_vector[0]
    first_result = output_vector[0]

    if stateful:
        sources = tuple(InitializedPublisher(*to_args(v)) for v in input_vector[0])
        input_vector = input_vector[1:]
        output_vector = output_vector[1:]
    else:
        sources = tuple(Publisher() for _ in input_vector[0])

    dut = cls(*sources, *args, **kwargs)

    collector = Collector()
    collector2 = Collector()

    # store result of .get() and check subscriptions before the first
    # subscription to dut is made
    stored_result = dut.get()

    assert all(len(source.subscriptions) == 0 for source in sources)
    assert len(dut.subscriptions) == 0

    # make first (permanent) subscription
    dispose_collector = dut.subscribe(collector)

    # at least one subscription of the source publishers
    stored_subscription_pattern = tuple(len(source.subscriptions) for source in sources)
    assert any(len(source.subscriptions) == 1 for source in sources)
    assert all(len(source.subscriptions) in (0, 1) for source in sources)
    assert len(dut.subscriptions) == 1

    # check .get() after subscription (should not change)
    assert dut.get() == stored_result

    # check emitted values after subscription
    if stateful and first_result != NONE:
        assert collector.state == unpack_args(*stored_result)
        with dut.subscribe(collector2):
            assert len(dut.subscriptions) == 2
            assert stored_subscription_pattern == tuple(len(source.subscriptions) for source in sources)
            assert collector2.state == unpack_args(*stored_result)
        assert len(dut.subscriptions) == 1
        assert stored_subscription_pattern == tuple(len(source.subscriptions) for source in sources)
        assert (collector2.state_vector == collector.state_vector)
    else:
        assert initial_state == stored_result
        assert initial_state == (to_args(collector.state) if initial_state else None)
        with dut.subscribe(collector2):
            assert len(dut.subscriptions) == 2
            assert stored_subscription_pattern == tuple(len(source.subscriptions) for source in sources)
            assert stored_result == (to_args(collector2.state) if initial_state else None)
        assert len(collector.state_vector) == (1 if initial_state else 0)
        assert len(collector2.state_vector) == (1 if initial_state else 0)

    assert dut.get() == stored_result

    # check with input vector
    stored_last_result = stored_result

    for v_emits, v_result in zip(input_vector, output_vector):
        stored_collector_len = len(collector)
        stored_collector2_len = len(collector2)

        for source, v_emit in zip(sources, v_emits):
            if v_emit is not NONE:
                source.notify(*to_args(v_emit))

        stored_result = dut.get()

        if v_result is NONE:
            with dut.subscribe(collector2):
                pass
            if has_state and stored_last_result is not None:
                assert collector.state == unpack_args(*stored_result)
                assert collector2.state == unpack_args(*stored_result)
                assert collector2.state == (None if stored_last_result is None else unpack_args(*stored_last_result))
                assert len(collector2) == stored_collector2_len + 1
            else:
                assert stored_result is None
                assert len(collector2) == stored_collector2_len
        else:
            assert collector.state == v_result
            if has_state or stateful:
                assert collector.state == unpack_args(*stored_result)
                with dut.subscribe(collector2):
                    assert collector2.state == v_result
                assert len(collector2) == stored_collector2_len + 1
            else:
                assert stored_result is None
                with dut.subscribe(collector2):
                    assert len(collector2) == stored_collector2_len

            assert len(collector) == stored_collector_len + 1

        stored_last_result = stored_result

    # dispose permanent subscriber
    collector.reset()
    collector2.reset()
    dispose_collector.dispose()

    if stateful:
        for source, v_emit in zip(sources, first_input):
            if v_emit is NONE:
                source.reset(*to_args(v_emit))
            else:
                source.notify(*to_args(v_emit))

    stored_result = dut.get()

    assert all(len(source.subscriptions) == 0 for source in sources)
    assert len(dut.subscriptions) == 0

    # make first (permanent) subscription
    dispose_collector = dut.subscribe(collector)

    # at least one subscription of the source publishers
    stored_subscription_pattern = tuple(len(source.subscriptions) for source in sources)
    assert any(len(source.subscriptions) == 1 for source in sources)
    assert all(len(source.subscriptions) in (0, 1) for source in sources)
    assert len(dut.subscriptions) == 1

    # check .get() after subscription (should not change)
    assert dut.get() == stored_result

    # check emitted values after subscription
    if stateful and first_result != NONE:
        assert collector.state == unpack_args(*stored_result)
        with dut.subscribe(collector2):
            assert len(dut.subscriptions) == 2
            assert stored_subscription_pattern == tuple(len(source.subscriptions) for source in sources)
            assert collector2.state == unpack_args(*stored_result)
        assert len(dut.subscriptions) == 1
        assert stored_subscription_pattern == tuple(len(source.subscriptions) for source in sources)
        assert (collector2.state_vector == collector.state_vector)
    else:
        assert stored_result == (to_args(collector.state) if stored_result else None)
        with dut.subscribe(collector2):
            assert len(dut.subscriptions) == 2
            assert stored_subscription_pattern == tuple(len(source.subscriptions) for source in sources)
            assert stored_result == (to_args(collector2.state) if stored_result else None)
        assert len(collector.state_vector) == (1 if stored_result else 0)
        assert len(collector2.state_vector) == (1 if stored_result else 0)

    assert dut.get() == stored_result

JITTER = 0.005

async def check_async_operator_coro(cls, args, kwargs, input_vector, output_vector, initial_state=None, has_state=False, loop=None):
    await check_operator_coro(cls, args, kwargs, input_vector, output_vector, initial_state=initial_state, has_state=has_state, stateful=False, loop=loop)
    await check_operator_coro(cls, args, kwargs, input_vector, output_vector, initial_state=initial_state, has_state=has_state, stateful=True, loop=loop)

async def check_operator_coro(cls, args, kwargs, input_vector, output_vector, initial_state=None, has_state=False, stateful=False, loop=None):
    if stateful:
        source = InitializedPublisher(*to_args(input_vector[0]))
        assert input_vector[0][0] == 0  # first entry has to be on timestamp 0
        input_vector = input_vector[1:]
    else:
        source = Publisher()

    dut = cls(source, *args, **kwargs)

    collector = Collector(loop=loop)
    collector2 = Collector(loop=loop)

    # store result of .get() and check subscriptions before the first
    # subscription to dut is made
    stored_result = dut.get()

    assert len(source.subscriptions) == 0
    assert len(dut.subscriptions) == 0

    # make first (permanent) subscription
    dispose_collector = dut.subscribe(collector)

    # at least one subscription of the source publishers
    assert len(source.subscriptions) == 1
    assert len(dut.subscriptions) == 1

    # check .get() after subscription (should not change)
    assert dut.get() == stored_result

    # check emitted values after subscription
    if stateful and output_vector[0][0] == 0:
        print(stored_result)
        assert collector.state == unpack_args(*stored_result)
        with dut.subscribe(collector2):
            assert len(dut.subscriptions) == 2
            assert collector2.state == unpack_args(*stored_result)
        assert len(dut.subscriptions) == 1
        assert (collector2.state_vector == collector.state_vector)
    else:
        assert initial_state == stored_result
        assert initial_state == (to_args(collector.state) if initial_state else None)
        with dut.subscribe(collector2):
            assert len(dut.subscriptions) == 2
            assert stored_result == (to_args(collector2.state) if initial_state else None)
        assert len(collector.state_vector) == (1 if initial_state else 0)
        assert len(collector2.state_vector) == (1 if initial_state else 0)

    assert dut.get() == stored_result

    # check with input vector

    last_timestamp = 0
    start_timestamp = loop.time()
    target_timestamp = start_timestamp

    for timestamp, value in input_vector:
        await asyncio.sleep(target_timestamp - loop.time() + timestamp - last_timestamp)
        target_timestamp += timestamp - last_timestamp
        last_timestamp = timestamp

        source.notify(*to_args(value))

    await asyncio.sleep(target_timestamp - loop.time() + output_vector[-1][0] - last_timestamp + 2*JITTER)
    for value_actual, timestamp_actual, (timestamp_target, value_target) in zip(collector.state_vector, collector.timestamp_vector, output_vector):
        assert abs(timestamp_actual-timestamp_target)<JITTER
        assert value_actual == value_target
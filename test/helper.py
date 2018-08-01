import asyncio
from typing import Any

from broqer import Subscriber, Publisher, SubscriptionDisposable

class Collector(Subscriber):
    def __init__(self, loop=None):
        Subscriber.__init__(self)
        self._result_vector = []
        if loop is not None:
            self._timestamp_vector = []
            self._start_timestamp = loop.time()
        self._loop = loop

    def emit(self, value: Any, who: Publisher) -> None:
        self._result_vector.append(value)
        if self._loop is not None:
            self._timestamp_vector.append(self._loop.time() - self._start_timestamp)

    @property
    def result_vector(self):
        return tuple(self._result_vector)

    @property
    def timestamp_vector(self):
        return tuple(self._timestamp_vector)

    def reset(self):
        """clear the result_vector"""
        self._result_vector.clear()
        if self._loop is not None:
            self._timestamp_vector.clear()
            self._start_timestamp = self._loop.time()

    def reset_timestamp(self):
        self._start_timestamp = self._loop.time()

    def __len__(self):
        return len(self._result_vector)

    @property
    def last_result(self):
        """returns the last last_result in result_vector"""
        return self._result_vector[-1]

    @property
    def timestamp(self):
        return self._timestamp_vector[-1]


class NONE:
    pass


class InitializedPublisher(Publisher):
    def __init__(self, init):
        Publisher.__init__(self)
        self._state = init

    def subscribe(self, subscriber: 'Subscriber') -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber)
        if self._state is not NONE :
            subscriber.emit(self._state, who=self)
        return disposable

    def get(self):
        if self._state is NONE:
            return Publisher.get(self)
        return self._state

    def reset(self, init):
        self._state = init

    def notify(self, value: Any) -> None:
        self._state = value
        Publisher.notify(self, value)

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
        sources = tuple(InitializedPublisher(v) for v in input_vector[0])
        input_vector = input_vector[1:]
        output_vector = output_vector[1:]
    else:
        sources = tuple(Publisher() for _ in input_vector[0])

    dut = cls(*sources, *args, **kwargs)

    collector_permanent = Collector()
    collector_temporary = Collector()

    # store result of .get() and check subscriptions before the first
    # subscription to dut is made
    try:
        stored_result = dut.get()
    except ValueError:
        stored_result = None

    assert all(len(source.subscriptions) == 0 for source in sources)
    assert len(dut.subscriptions) == 0

    # make first (permanent) subscription
    dispose_collector_permanent = dut.subscribe(collector_permanent)

    # at least one subscription of the source publishers
    stored_subscription_pattern = tuple(len(source.subscriptions) for source in sources)
    assert any(len(source.subscriptions) == 1 for source in sources)
    assert all(len(source.subscriptions) in (0, 1) for source in sources)
    assert len(dut.subscriptions) == 1

    # check .get() after subscription (should not change)
    try:
        assert dut.get() == stored_result
    except ValueError:
        assert stored_result is None

    # check emitted values after subscription
    if stateful and first_result != NONE:
        assert collector_permanent.last_result == stored_result
        with dut.subscribe(collector_temporary):
            assert len(dut.subscriptions) == 2
            assert stored_subscription_pattern == tuple(len(source.subscriptions) for source in sources)
            assert collector_temporary.last_result == stored_result
        assert len(dut.subscriptions) == 1
        assert stored_subscription_pattern == tuple(len(source.subscriptions) for source in sources)
        assert (collector_temporary.result_vector == collector_permanent.result_vector)
    else:
        assert initial_state == stored_result
        assert initial_state == (collector_permanent.last_result if initial_state else None)
        with dut.subscribe(collector_temporary):
            assert len(dut.subscriptions) == 2
            assert stored_subscription_pattern == tuple(len(source.subscriptions) for source in sources)
            assert stored_result == (collector_temporary.last_result if initial_state else None)
        assert len(collector_permanent.result_vector) == (1 if initial_state else 0)
        assert len(collector_temporary.result_vector) == (1 if initial_state else 0)

    # check with input vector
    stored_last_result = stored_result

    for v_emits, v_result in zip(input_vector, output_vector):
        stored_collector_permanent_len = len(collector_permanent)
        stored_collector_temporary_len = len(collector_temporary)

        for source, v_emit in zip(sources, v_emits):
            if v_emit is not NONE:
                source.notify(v_emit)

        try:
            stored_result = dut.get()
        except ValueError:
            stored_result = None

        if v_result is NONE:
            with dut.subscribe(collector_temporary):
                pass
            if has_state is None:
                pass
            elif has_state and stored_last_result is not None:
                assert collector_permanent.last_result == stored_result
                assert collector_temporary.last_result == stored_result
                assert len(collector_temporary) == stored_collector_temporary_len + 1
            else:
                assert stored_result is None
                assert len(collector_temporary) == stored_collector_temporary_len
        else:
            assert collector_permanent.last_result == v_result
            if has_state is None:  # special case for undefined behavior
                pass
            elif has_state or stateful:
                assert collector_permanent.last_result == stored_result
                with dut.subscribe(collector_temporary):
                    assert collector_temporary.last_result == v_result
                assert len(collector_temporary) == stored_collector_temporary_len + 1
            else:
                assert stored_result is None
                with dut.subscribe(collector_temporary):
                    assert len(collector_temporary) == stored_collector_temporary_len

            assert len(collector_permanent) == stored_collector_permanent_len + 1

        stored_last_result = stored_result

    # dispose permanent subscriber
    collector_permanent.reset()
    collector_temporary.reset()
    dispose_collector_permanent.dispose()

    if stateful:
        for source, v_emit in zip(sources, first_input):
            if v_emit is NONE:
                source.reset(v_emit)
            else:
                source.notify(v_emit)

    try:
        stored_result = dut.get()
    except ValueError:
        stored_result = None

    assert all(len(source.subscriptions) == 0 for source in sources)
    assert len(dut.subscriptions) == 0

    # make first (permanent) subscription
    dispose_collector_permanent = dut.subscribe(collector_permanent)

    # at least one subscription of the source publishers
    stored_subscription_pattern = tuple(len(source.subscriptions) for source in sources)
    assert any(len(source.subscriptions) == 1 for source in sources)
    assert all(len(source.subscriptions) in (0, 1) for source in sources)
    assert len(dut.subscriptions) == 1

    # check .get() after subscription (should not change)
    try:
        assert dut.get() == stored_result
    except ValueError:
        assert stored_result is None

    # check emitted values after subscription
    if stateful and first_result != NONE:
        assert collector_permanent.last_result == stored_result
        with dut.subscribe(collector_temporary):
            assert len(dut.subscriptions) == 2
            assert stored_subscription_pattern == tuple(len(source.subscriptions) for source in sources)
            assert collector_temporary.last_result == stored_result
        assert len(dut.subscriptions) == 1
        assert stored_subscription_pattern == tuple(len(source.subscriptions) for source in sources)
        assert (collector_temporary.result_vector == collector_permanent.result_vector)
    else:
        assert stored_result == (collector_permanent.last_result if stored_result else None)
        with dut.subscribe(collector_temporary):
            assert len(dut.subscriptions) == 2
            assert stored_subscription_pattern == tuple(len(source.subscriptions) for source in sources)
            assert stored_result == (collector_temporary.last_result if stored_result else None)
        assert len(collector_permanent.result_vector) == (1 if stored_result else 0)
        assert len(collector_temporary.result_vector) == (1 if stored_result else 0)

    try:
        assert dut.get() == stored_result
    except ValueError:
        assert stored_result is None

JITTER = 0.015

async def check_async_operator_coro(cls, args, kwargs, input_vector, output_vector, initial_state=None, has_state=False, loop=None):
    await check_operator_coro(cls, args, kwargs, input_vector, output_vector, initial_state=initial_state, has_state=has_state, stateful=False, loop=loop)
    await check_operator_coro(cls, args, kwargs, input_vector, output_vector, initial_state=initial_state, has_state=has_state, stateful=True, loop=loop)

async def check_operator_coro(cls, args, kwargs, input_vector, output_vector, initial_state=None, has_state=False, stateful=False, loop=None):
    assert input_vector[0][0] == 0  # first entry has to be on timestamp 0
    first_input_value = input_vector[0][1]
    input_vector = input_vector[1:]

    if stateful:
        source = InitializedPublisher(first_input_value)
    else:
        source = Publisher()

    dut = cls(source, *args, **kwargs)

    collector_permanent = Collector(loop=loop)
    collector_temporary = Collector(loop=loop)

    # store result of .get() and check subscriptions before the first
    # subscription to dut is made
    try:
        stored_result = dut.get()
    except ValueError:
        stored_result = None

    assert len(source.subscriptions) == 0
    assert len(dut.subscriptions) == 0

    # make first (permanent) subscription
    dispose_collector_permanent = dut.subscribe(collector_permanent)

    # at least one subscription of the source publishers
    assert len(source.subscriptions) == 1
    assert len(dut.subscriptions) == 1

    # check .get() after subscription (should not change)
    try:
        assert dut.get() == stored_result
    except ValueError:
        assert stored_result is None

    # check emitted values after subscription
    if stateful and output_vector[0][0] == 0:
        print(stored_result)
        assert collector_permanent.last_result == stored_result
        with dut.subscribe(collector_temporary):
            assert len(dut.subscriptions) == 2
            assert collector_temporary.last_result == stored_result
        assert len(dut.subscriptions) == 1
        assert (collector_temporary.result_vector == collector_permanent.result_vector)
    else:
        with dut.subscribe(collector_temporary):
            assert len(dut.subscriptions) == 2
        assert len(dut.subscriptions) == 1

    if not stateful:
        source.notify(first_input_value)

    # check with input vector
    failed_list = []

    def _check_temporary(timestamp, value):
        result = dut.get()
        collector_temporary_len = len(collector_temporary.result_vector)
        with dut.subscribe(collector_temporary):
            assert len(source.subscriptions) == 1
            assert len(dut.subscriptions) == 2
        assert len(source.subscriptions) == 1
        assert len(dut.subscriptions) == 1
        if has_state:
            if collector_temporary.last_result != value or len(collector_temporary) != collector_temporary_len + 1:
                failed_list.append( ('SUBSCRIBE', timestamp, value, result) )
            if result != value or collector_temporary.last_result != result:
                failed_list.append( ('GET', timestamp, value, result) )
        else:
            if len(collector_temporary) != collector_temporary_len:
                failed_list.append( ('SUBSCRIBE', timestamp, value, result) )
            if result is not None:
                failed_list.append( ('GET', timestamp, value, result) )

    for timestamp, value in input_vector:
        loop.call_later(timestamp, source.notify, value)

    for timestamp, value in output_vector:
        loop.call_later(timestamp + JITTER, _check_temporary, timestamp, value)

    collector_permanent.reset_timestamp()
    collector_temporary.reset_timestamp()

    await asyncio.sleep(output_vector[-1][0] + 2*JITTER)

    for value_actual, timestamp_actual, (timestamp_target, value_target) in zip(collector_permanent.result_vector, collector_permanent.timestamp_vector, output_vector):
        print(timestamp_target, timestamp_actual, value_target, value_actual)
        assert abs(timestamp_actual-timestamp_target)<JITTER
        assert value_actual == value_target
    print(collector_permanent.result_vector, collector_permanent.timestamp_vector)
    assert len(collector_permanent.result_vector) == len(output_vector)

    assert not failed_list

    # dispose permanent subscriber
    collector_permanent.reset()
    collector_temporary.reset()
    dispose_collector_permanent.dispose()

    if stateful:
        source.reset(first_input_value)

    try:
        stored_result = dut.get()
    except ValueError:
        stored_result = None

    assert len(source.subscriptions) == 0
    assert len(dut.subscriptions) == 0

    # re-make permanent subscription
    dispose_collector_permanent = dut.subscribe(collector_permanent)

    # at least one subscription of the source publishers
    assert len(source.subscriptions) == 1
    assert len(dut.subscriptions) == 1

    # check .get() after subscription (should not change)
    try:
        assert dut.get() == stored_result
    except ValueError:
        assert stored_result is None

import pytest

from broqer import Hub, op, Value


def test_freeze():
    hub = Hub()

    hub.assign('value1', op.Just(0))

    assert 'value1' in hub

    hub.freeze()

    assert len(tuple(hub)) == 1

    hub.freeze(False)

    hub['value2'] | op.sink()
    hub['value3'].emit(1)

    assert 'value2' in hub
    assert 'value3' in hub

    with pytest.raises(ValueError):
        hub.freeze()

    hub.assign('value2', Value(0))
    hub.assign('value3', Value(0))

    hub.freeze()

    with pytest.raises(ValueError):
        hub.assign('value4', op.Just(0))

    with pytest.raises(ValueError):
        hub['value5'] | op.sink()

    with pytest.raises(ValueError):
        hub['value6'].emit(1)

    assert len(tuple(hub)) == 3

    hub.freeze(False)

    hub['value4'] | op.sink()
    hub.assign('value5', op.Just(0))
    hub['value6'].emit(1)

    assert 'value4' in hub
    assert 'value5' in hub
    assert 'value6' in hub

    assert len(tuple(hub)) == 6

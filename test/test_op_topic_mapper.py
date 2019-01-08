from unittest import mock
import pytest

from broqer import Disposable, Hub, Value
from broqer.hub.utils import TopicMapper
from broqer.subject import Subject


def test_topic_mapper():
    d = dict()
    hub = Hub()

    hub['topic1'].assign(Value(0))
    hub['topic2'].assign(Subject())

    mapper_instance = TopicMapper(d)

    assert not d
    hub['topic1'] | mapper_instance
    assert d == {'topic1':0}

    hub['topic2'] | mapper_instance
    assert d == {'topic1':0}

    hub['topic2'].emit(2)
    assert d == {'topic1':0, 'topic2':2}

    hub['topic1'].emit(1)
    assert d == {'topic1':1, 'topic2':2}

    with pytest.raises(TypeError):
        Value(0) | mapper_instance
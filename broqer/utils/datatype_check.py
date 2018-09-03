import asyncio
from typing import Any

from broqer import Subscriber
from broqer.hub import Hub, MetaTopic


def resolve_meta_key(hub, key, meta):
    if key not in meta:
        return None
    value = meta[key]
    if isinstance(value, str) and value[0] == '>':
        topic = value[1:]
        if topic not in hub:
            raise KeyError('topic %s not found in hub' % topic)
        return hub[topic].get()
    return value


class DT:
    def cast(self, topic, value):  # pylint: disable=no-self-use,W0613
        return value

    def check(self, topic, value):  # pylint: disable=no-self-use,W0613
        pass


class NumberDT(DT):
    """ Datatype for general numbers

    Recognized meta keys:
    * minimum: check the value against this minimum (below raises an Exception)
    * maximum: check against maximum (above raises an Exception)
    """

    def check(self, topic, value):
        minimum = resolve_meta_key(topic.hub, 'minimum', topic.meta)
        if minimum is not None and value < minimum:
            raise ValueError('Value %d under minimum of %d' % (value, minimum))

        maximum = resolve_meta_key(topic.hub, 'maximum', topic.meta)
        if maximum is not None and value > maximum:
            raise ValueError('Value %d over maximum of %d' % (value, maximum))


class IntegerDT(NumberDT):
    def cast(self, topic, value):
        return int(value)

    def check(self, topic, value):
        NumberDT.check(self, topic, value)
        if not isinstance(value, int):
            raise ValueError('%r is not an integer' % value)


class FloatDT(NumberDT):
    def cast(self, topic, value):
        return float(value)

    def check(self, topic, value):
        NumberDT.check(self, topic, value)
        if not isinstance(value, float):
            raise ValueError('%r is not a float' % value)


class DTTopic(MetaTopic):
    def __init__(self, hub: Hub, path: str) -> None:
        MetaTopic.__init__(self, hub, path)
        self._hub = hub

    def cast(self, value):
        '''Will cast value to the given datatype. It will not check the
        value.
        '''
        return self._hub.topic_factory.cast(self, value)

    def check(self, value):
        '''Check the value against the datatype and limits defined in meta
        dictionary. The value has to be in the appropriate datatype (may use
        cast before)
        '''
        self._hub.topic_factory.check(self, value)

    def checked_emit(self, value: Any) -> asyncio.Future:

        assert isinstance(self._subject, Subscriber), \
            'Topic has to be a subscriber'

        value = self.cast(value)
        self.check(value)
        return self._subject.emit(value, who=self)

    @property
    def hub(self):
        return self._hub


class DTRegistry:
    def __init__(self):
        self._datatypes = {
            'none': DT(),
            'int': IntegerDT(),
            'float': FloatDT(),
            'str': DT()
        }

    def add_datatype(self, name: str, datatype: DT):
        self._datatypes[name] = datatype

    def __call__(self, hub: Hub, path: str) -> DTTopic:
        return DTTopic(hub, path)

    def cast(self, topic, value):
        datatype_key = topic.meta.get('datatype', 'none')
        return self._datatypes[datatype_key].cast(topic, value)

    def check(self, topic, value):
        datatype_key = topic.meta.get('datatype', 'none')
        self._datatypes[datatype_key].check(topic, value)
        if 'validate' in topic.meta:
            self._datatypes[topic.meta['validate']].check(topic, value)

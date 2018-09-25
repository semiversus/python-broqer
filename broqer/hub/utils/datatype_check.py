""" Implements DTRegistry and common DTs """
import asyncio
from typing import Any

from broqer import Subscriber
from broqer.hub import Hub, MetaTopic


def resolve_meta_key(hub, key, meta):
    """ Resolve a value when it's a string and starts with '>' """
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
    """ Base class for a datatype """
    def cast(self, topic, value):  # pylint: disable=no-self-use,W0613
        """ Casting a string to the appropriate datatype """
        return value

    def check(self, topic, value):  # pylint: disable=no-self-use,W0613
        """ Checking the value if it fits into the given specification """
        pass


class NumberDT(DT):
    """ Datatype for general numbers

    Recognized meta keys:
    * lower_input_limit: check the value against minimum (below->Exception)
    * upper_input_limit: check against maximum (above raises an Exception)
    """

    def check(self, topic, value):
        minimum = resolve_meta_key(topic.hub, 'lower_input_limit', topic.meta)
        if minimum is not None and value < minimum:
            raise ValueError('Value %r under minimum of %r' % (value, minimum))

        maximum = resolve_meta_key(topic.hub, 'upper_input_limit', topic.meta)
        if maximum is not None and value > maximum:
            raise ValueError('Value %r over maximum of %r' % (value, maximum))


class IntegerDT(NumberDT):
    """ Datatype to represant integers """
    def cast(self, topic, value):
        return int(value)

    def check(self, topic, value):
        NumberDT.check(self, topic, value)
        if not isinstance(value, int):
            raise ValueError('%r is not an integer' % value)


class FloatDT(NumberDT):
    """ Datatype for floating point numbers """
    def cast(self, topic, value):
        return float(value)

    def check(self, topic, value):
        NumberDT.check(self, topic, value)
        if not isinstance(value, float):
            raise ValueError('%r is not a float' % value)


class DTTopic(MetaTopic):
    """ Topic with additional datatype check functionality """
    def __init__(self, hub: Hub, path: str) -> None:
        MetaTopic.__init__(self, hub, path)

    def cast(self, value):
        """ Will cast value to the given datatype. It will not check the
        value.
        """
        return self._hub.topic_factory.cast(self, value)

    def check(self, value):
        """ Check the value against the datatype and limits defined in meta
        dictionary. The value has to be in the appropriate datatype (may use
        cast before)
        """
        self._hub.topic_factory.check(self, value)

    def checked_emit(self, value: Any) -> asyncio.Future:
        """ Casting and checking in one call """

        assert isinstance(self._subject, Subscriber), \
            'Topic has to be a subscriber'

        value = self.cast(value)
        self.check(value)
        return self._subject.emit(value, who=self)


class DTRegistry:
    """ Registry used as topic factory for hub """
    def __init__(self):
        self._datatypes = {
            'none': DT(),
            'int': IntegerDT(),
            'float': FloatDT(),
            'str': DT()
        }

    def add_datatype(self, name: str, datatype: DT):
        """ Register the datatype with it's name """
        self._datatypes[name] = datatype

    def __call__(self, hub: Hub, path: str) -> DTTopic:
        return DTTopic(hub, path)

    def cast(self, topic, value):
        """ Cast a string to the value based on the datatype """
        datatype_key = topic.meta.get('datatype', 'none')
        result = self._datatypes[datatype_key].cast(topic, value)
        validate_dt = topic.meta.get('validate', None)
        if validate_dt:
            result = self._datatypes[validate_dt].cast(topic, result)
        return result

    def check(self, topic, value):
        """ Checking the value if it fits into the given specification """
        datatype_key = topic.meta.get('datatype', 'none')
        self._datatypes[datatype_key].check(topic, value)
        validate_dt = topic.meta.get('validate', None)
        if validate_dt:
            self._datatypes[validate_dt].check(topic, value)
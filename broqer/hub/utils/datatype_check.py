""" Implements DTRegistry and common DTs """
import asyncio
from ast import literal_eval
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


class NumberDT(DT):
    """ Datatype for general numbers

    Recognized meta keys:
    - lower_input_limit: check the value against minimum (below->Exception)
    - upper_input_limit: check against maximum (above raises an Exception)
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
        if not isinstance(value, (int, float)):
            raise ValueError('%r is not a float' % value)


class BooleanDT(DT):
    """ Datatype for booleans """

    true_tuple = (True, 'True', '1')
    false_tuple = (False, 'False', '0')

    def cast(self, topic, value):
        if value in BooleanDT.true_tuple:
            return True
        if value in BooleanDT.false_tuple:
            return False
        raise TypeError('Value %r is not a boolean' % value)


class ListDT(DT):
    """ Datatype for lists """

    def cast(self, topic, value):
        if isinstance(value, str):
            value = literal_eval(value)
        if isinstance(value, (list, tuple)):
            return value
        raise TypeError('Value %r is not a list' % value)

    def check(self, topic, value):
        minimum_size = resolve_meta_key(topic.hub, 'minimum_size', topic.meta)
        if minimum_size is not None and len(value) < minimum_size:
            raise ValueError('Value %r needs to have at least %d elements' %
                             (value, minimum_size))

        maximum_size = resolve_meta_key(topic.hub, 'maximum_size', topic.meta)
        if maximum_size is not None and len(value) > maximum_size:
            raise ValueError('Value %r needs to have at most %d elements' %
                             (value, maximum_size))

        item_dt_str = resolve_meta_key(topic.hub, 'item_datatype', topic.meta)
        if item_dt_str is not None:
            item_dt = topic.hub.topic_factory.resolve_datatype(item_dt_str)
            for index, item in enumerate(value):
                try:
                    item_dt.check(topic, item)
                except ValueError:
                    raise ValueError('Element %d in %r is not a valid %s' %
                                     (index, value, item_dt_str))


class TableDT(DT):
    """ Datatype for tables """

    def cast(self, topic, value):
        if isinstance(value, str):
            value = literal_eval(value)
        if isinstance(value, (list, tuple)):
            return value
        raise TypeError('Value %r is not a table' % value)

    def check(self, topic, value):
        minimum_rows = resolve_meta_key(topic.hub, 'minimum_rows', topic.meta)
        if minimum_rows is not None and len(value) < minimum_rows:
            raise ValueError('Value %r needs to have at least %d rows' %
                             (value, minimum_rows))

        maximum_rows = resolve_meta_key(topic.hub, 'maximum_rows', topic.meta)
        if maximum_rows is not None and len(value) > maximum_rows:
            raise ValueError('Value %r needs to have at most %d rows' %
                             (value, maximum_rows))

        minimum_cols = resolve_meta_key(topic.hub, 'minimum_cols', topic.meta)
        if minimum_cols is not None and value \
                and len(value[0]) < minimum_cols:
            raise ValueError('Value %r needs to have at least %d columns' %
                             (value, minimum_cols))

        maximum_cols = resolve_meta_key(topic.hub, 'maximum_cols', topic.meta)
        if maximum_cols is not None and value and \
                len(value[0]) > maximum_cols:
            raise ValueError('Value %r needs to have at most %d columns' %
                             (value, maximum_cols))

        if value:
            for row in value:
                if not isinstance(row, (tuple, list)):
                    raise ValueError('Rows have to be tuples or lists')
                if len(row) != len(value[0]):
                    raise ValueError('Number of columns have to be uniform')


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

        if not isinstance(self._subject, Subscriber):
            raise TypeError('Topic %r has to be a subscriber' % self._path)

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
            'boolean': BooleanDT(),
            'list': ListDT(),
            'table': TableDT(),
            'str': DT()
        }

    def add_datatype(self, name: str, datatype: DT):
        """ Register the datatype with it's name """
        self._datatypes[name] = datatype

    def resolve_datatype(self, name: str):
        """ Returns the datatype described by name """
        return self._datatypes[name]

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

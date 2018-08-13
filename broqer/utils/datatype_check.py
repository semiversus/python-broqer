import asyncio
from typing import Any

from broqer.hub import MetaTopic

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
    def cast(self, _hub, value, _meta):
        return value

    def check(self, _hub, _value, _meta):
        pass

class NumberDT(DT):
    """ Datatype for general numbers

    Recognized meta keys:
    * minimum: check the value against this minimum (below raises an Exception)
    * maximum: check against maximum (above raises an Exception)
    """

    def check(self, hub, value, meta):
        minimum = resolve_meta_key(hub, 'minimum', meta)
        if minimum is not None and value < minimum:
            raise ValueError('Value %d under minimum of %d' % (value, minimum))

        maximum = resolve_meta_key(hub, 'maximum', meta)
        if maximum is not None and value > maximum:
            raise ValueError('Value %d over maximum of %d' % (value, maximum))

class IntegerDT(NumberDT):
    def cast(self, _hub, value, _meta):
        return int(value)

    def check(self, hub, value, meta):
        NumberDT.check(self, hub, value, meta)
        if not isinstance(value, int):
            raise ValueError('%r is not an integer'%value)

class FloatDT(NumberDT):
    def cast(self, _hub, value, _meta):
        return float(value)

    def check(self, hub, value, meta):
        NumberDT.check(self, hub, value, meta)
        if not isinstance(value, float):
            raise ValueError('%r is not a float'%value)

class DTTopic(MetaTopic):
    def __init__(self, hub: 'Hub', path: str) -> None:
        MetaTopic.__init__(self, hub, path)
        self._hub = hub

    def cast(self, value):
        '''Will cast value to the given datatype. It will not check the
        value.
        '''
        return self._hub.topic_factory.cast(self._hub, value, self._meta)

    def check(self, value):
        '''Check the value against the datatype and limits defined in meta
        dictionary. The value has to be in the appropriate datatype (may use
        cast before)
        '''
        self._hub.topic_factory.check(self._hub, value, self._meta)

    def checked_emit(self, value: Any) -> asyncio.Future:
        value = self.cast(value)
        self.check(value)
        return self._subject.emit(value, who=self)

class DTRegistry:
    def __init__(self):
        self._datatypes = {
            'none': DT(),
            'integer': IntegerDT(),
            'float': FloatDT(),
            'string': DT()
        }

    def add_datatype(self, name: str, dt: DT):
        self._datatypes[name] = dt

    def __call__(self, hub: 'Hub', path: str) -> None:
        return DTTopic(hub, path)

    def cast(self, hub, value, meta):
        datatype_key = meta.get('datatype', 'none')
        return self._datatypes[datatype_key].cast(hub, value, meta)

    def check(self, hub, value, meta):
        datatype_key = meta.get('datatype', 'none')
        self._datatypes[datatype_key].check(hub, value, meta)
        if 'validate' in meta:
            self._datatypes[meta['validate']].check(hub, value, meta)
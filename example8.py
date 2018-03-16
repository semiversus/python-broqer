from broqer.stream import Stream
from broqer import op
import asyncio

d=dict()

value1=Stream() | op.update_dict(d, 'value1')
value2=Stream() | op.update_dict(d, 'value2')

value1.emit('abc')
for i in range(10):
  value2.emit(i)

print(repr(d))
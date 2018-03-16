from broqer.stream import Stream
from broqer import op
import asyncio

value=Stream()

async def main():
  print('Value:', await (value|op.as_future()) )
  print('Value:', await value.as_future() )
  print('Value:', await value )
  print(value._subscriptions)

loop=asyncio.get_event_loop()

loop.call_later(0.2, value.emit, 1)
loop.call_later(0.4, value.emit, 2)
loop.call_later(0.6, value.emit, 3)

loop.run_until_complete(main())
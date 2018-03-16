from broqer.stream import Stream
from broqer import op
import asyncio
from functools import partial

async def delay_coro(value):
  await asyncio.sleep(1)
  return value

value=Stream()
value | op.sink(print)
value | op.map_async(delay_coro) | op.sink(lambda v:print('Delayed:',v))

async def main():
  for i in range(10):
    value.emit(i)
    await asyncio.sleep(0.3)
  await asyncio.sleep(1.5)

loop=asyncio.get_event_loop()
loop.run_until_complete(main())
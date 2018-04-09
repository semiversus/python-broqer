from broqer.subject import Subject
from broqer import op
import asyncio

value=Subject()

async def main():
  print('Value:', await (value|op.to_future()) )
  print('Value:', await value )
  print(value._subscriptions)

loop=asyncio.get_event_loop()

loop.call_later(0.2, value.emit, 1)
loop.call_later(0.4, value.emit, 2)

loop.run_until_complete(main())
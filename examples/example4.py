from broqer.subject import Subject
from broqer import op
import asyncio

adc_raw=Subject().setup(0)

( adc_raw  
  | op.map(lambda d:d*5+3)
  | op.sample(0.3)
  | op.sink(print)
)
        

async def main():
  await asyncio.sleep(0.5)
  adc_raw.emit(50)
  await asyncio.sleep(2)

loop=asyncio.get_event_loop()
loop.run_until_complete(main())
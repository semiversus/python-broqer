import asyncio
import subprocess
import operator

from broqer import op

(op.FromPolling(1, subprocess.check_output, 'uptime')
 | op.Map(str, encoding='utf - 8')
 | op.Map(str.split, sep=', ')
 | op.Map(lambda v:v[0])
 | op.Sink(print)
 )

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.sleep(10))

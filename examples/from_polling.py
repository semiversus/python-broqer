import asyncio
import subprocess
import operator

from broqer import op

(op.FromPolling(1, subprocess.check_output, 'uptime')
 | op.map_(str, encoding='utf - 8')
 | op.map_(str.split, sep=', ')
 | op.map_(lambda v:v[0])
 | op.Sink(print)
 )

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.sleep(10))

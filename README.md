# loopmon - Lightweight Event Loop monitoring

loopmon is a lightweight library that can detect throttling of event loops.
For example, you can detect long-running coroutine or whether the blocking function is invoked inside the event loop.


## Usage

```python
import asyncio
import time
from datetime import datetime
import loopmon

async def print_collected_data(lag: float, tasks: int, data_at: datetime) -> None:
    print(f'event loop lag: {lag:.3f}, running tasks: {tasks}, at {data_at}')

async def main() -> None:
    loopmon.create(interval=0.5, callbacks=[print_collected_data])
    # Simple I/O bound coroutine does not occur event loop lag
    await asyncio.sleep(0.2)
    # Blocking function call
    time.sleep(1)

if __name__ == '__main__':
    asyncio.run(main())
```

will prints:

```
event loop lag: 0.000, running tasks: 2, at 2022-02-24 13:29:05.367330+00:00
event loop lag: 1.001, running tasks: 1, at 2022-02-24 13:29:06.468622+00:00
```

You can check other [examples](https://github.com/isac322/loopmon/tree/master/examples).

I recommend you to add `loopmon.create(...)` on beginning of async function if you are not familiar with handling loop itself.
But you can also control creation, installation or staring of monitor via `EventLoopMonitor.start()` or `EventLoopMonitor.install_to_loop()`.

## Features

- Detects event loop lag
  - Detects event loop running on other thread. [example](https://github.com/isac322/loopmon/blob/master/examples/06_monitoring_another_thread.py)
- Collect how many tasks are running in the event loop
- Customize monitoring start and end points
- Customize monitoring interval
- Customize collected metrics through callbacks
- 100% type annotated
- Zero dependency (except `typing-extentions`)


## How it works

Event loop is single threaded and based on Cooperative Scheduling.
So if there is a task that does not yield to another tasks, any tasks on the loop can not be executed.
And starvation also happens when there are too many tasks that a event loop can not handle.

Currently `loopmon.SleepEventLoopMonitor` is one and only monitor implementation.
It periodically sleeps with remembering time just before sleep, and compares the time after awake.
The starvation happen if the difference bigger than its sleeping interval.


#### pseudo code of `SleepEventLoopMonitor`

```python
while True:
    before = loop.time()
    await asyncio.sleep(interval)
    lag = loop.time() - before - interval
    tasks = len(asyncio.all_tasks(loop))
    data_at = datetime.now(timezone.utc)
    for c in callbacks:
        loop.create_task(c(lag, tasks, data_at))
```

## Integration examples

### Prometheus


```python
from datetime import datetime
from functools import partial
import loopmon
from prometheus_client import Gauge

async def collect_lag(gauge: Gauge, lag: float, _: int, __: datetime) -> None:
    gauge.set(lag)

async def main(gauge: Gauge) -> None:
    loopmon.create(interval=0.5, callbacks=[partial(collect_lag, gauge)])
    ...
```
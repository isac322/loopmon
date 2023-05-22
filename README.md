# loopmon - Lightweight Event Loop monitoring


[![Codecov](https://img.shields.io/codecov/c/gh/isac322/loopmon?style=flat-square&logo=codecov)](https://app.codecov.io/gh/isac322/loopmon)
[![Dependabot Status](https://flat.badgen.net/github/dependabot/isac322/loopmon?icon=github)](https://github.com/isac322/loopmon/network/dependencies)
[![PyPI](https://img.shields.io/pypi/v/loopmon?label=pypi&logo=pypi&style=flat-square)](https://pypi.org/project/loopmon/)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/loopmon?style=flat-square&logo=pypi)](https://pypi.org/project/loopmon/)
[![Python Version](https://img.shields.io/pypi/pyversions/loopmon.svg?style=flat-square&logo=python)](https://pypi.org/project/loopmon/)
[![GitHub last commit (branch)](https://img.shields.io/github/last-commit/isac322/loopmon/master?logo=github&style=flat-square)](https://github.com/isac322/loopmon/commits/master)
[![GitHub Workflow Status (branch)](https://img.shields.io/github/actions/workflow/status/isac322/loopmon/ci.yml?branch=master&logo=github&style=flat-square)](https://github.com/isac322/loopmon/actions)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)](https://github.com/psf/black)

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
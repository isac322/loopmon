import asyncio
import time
from datetime import datetime
from functools import partial
from threading import Thread

import loopmon


async def print_collected_data(thread_name: str, lag: float, tasks: int, data_at: datetime) -> None:
    print(f'[{thread_name.upper():7s}] event loop lag: {lag:.3f}, running tasks: {tasks}, at {data_at}')


async def body_of_main_thread(mon: loopmon.EventLoopMonitor) -> None:
    # Main thread does not invoke any blocking function -> There should be no lag in the event loop.
    mon.install_to_loop()
    await asyncio.sleep(5)


async def body_of_another_thread(mon: loopmon.EventLoopMonitor) -> None:
    # Another thread invokes blocking function -> There should be lag.
    mon.install_to_loop()
    await asyncio.sleep(1)
    time.sleep(2)


if __name__ == '__main__':
    main_mon = loopmon.SleepEventLoopMonitor(
        interval=1,
        callbacks=[partial(print_collected_data, 'main')],
    )
    another_mon = loopmon.SleepEventLoopMonitor(
        interval=1,
        callbacks=[partial(print_collected_data, 'another')],
    )

    # It spawns another thread and runs a separate Event Loop.
    t = Thread(target=lambda m: asyncio.run(body_of_another_thread(m)), args=(another_mon,))
    t.start()
    # Runs Event Loop on main thread
    asyncio.run(body_of_main_thread(main_mon))
    t.join()

# Expected output
# -> The main thread can measure the lag independently without the influence of other threads.
#
# [MAIN   ] event loop lag: 0.000, running tasks: 2, at 2022-02-24 13:01:15.851714+00:00
# [MAIN   ] event loop lag: 0.001, running tasks: 2, at 2022-02-24 13:01:16.852284+00:00
# [MAIN   ] event loop lag: 0.001, running tasks: 2, at 2022-02-24 13:01:17.853442+00:00
# [ANOTHER] event loop lag: 2.003, running tasks: 1, at 2022-02-24 13:01:17.854732+00:00
# [MAIN   ] event loop lag: 0.001, running tasks: 2, at 2022-02-24 13:01:18.854604+00:00

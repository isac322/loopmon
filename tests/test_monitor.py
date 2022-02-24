from __future__ import annotations

import asyncio
import sys
import time
from contextlib import contextmanager
from threading import Thread
from typing import Generator

import pytest
from pytest_mock import MockerFixture

import loopmon


@contextmanager
def with_event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    yield loop

    loop.run_until_complete(asyncio.sleep(0))
    to_cancel = asyncio.tasks.all_tasks(loop)
    for t in to_cancel:
        t.cancel()
    results = loop.run_until_complete(asyncio.tasks.gather(*to_cancel, return_exceptions=True))
    assert all(not isinstance(r, BaseException) for r in results)
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()


def test_can_catch_loop_close() -> None:
    with with_event_loop() as loop:  # type: asyncio.AbstractEventLoop
        monitor = loopmon.create(loop)
        # Give loop time to run loopmon
        loop.run_until_complete(asyncio.sleep(0))
        assert monitor.running
    assert not monitor.running


def test_can_execute_callback(mocker: MockerFixture) -> None:
    interval = 0.01

    with with_event_loop() as loop:  # type: asyncio.AbstractEventLoop
        mock = mocker.AsyncMock()
        monitor = loopmon.create(loop, interval=interval, callbacks=(mock,))
        # Give loop time to run loopmon
        loop.run_until_complete(asyncio.sleep(interval * 1.5))
        assert monitor.running
        mock.assert_awaited_once()

    assert not monitor.running


def test_can_detect_lag_comes_from_block_call(mocker: MockerFixture) -> None:
    interval = 0.01
    blocking_delay = 0.1

    with with_event_loop() as loop:
        mock = mocker.AsyncMock()
        monitor = loopmon.create(loop, interval=interval, callbacks=(mock,))
        # Give loop time to run loopmon
        loop.run_until_complete(asyncio.sleep(0))
        assert monitor.running

        # Block whole python interpreter
        time.sleep(blocking_delay)
        # Give loop time to run loopmon
        loop.run_until_complete(asyncio.sleep(0))

        mock.assert_awaited_once()
        measured_lag = mock.await_args.args[0]
        # 10% margin
        assert blocking_delay * 0.9 <= measured_lag <= blocking_delay * 1.1

    assert not monitor.running


def test_can_not_install_to_closed_loop() -> None:
    loop = asyncio.new_event_loop()
    loop.close()

    with pytest.raises(ValueError):
        loopmon.create(loop)


def test_can_not_install_to_already_installed_loop() -> None:
    with with_event_loop() as loop:  # type: asyncio.AbstractEventLoop
        monitor = loopmon.create(loop)

        with pytest.raises(ValueError):
            monitor.install_to_loop(loop)


def test_can_not_double_start() -> None:
    with with_event_loop() as loop:  # type: asyncio.AbstractEventLoop
        monitor = loopmon.create(loop)
        # Give loop time to run loopmon
        loop.run_until_complete(asyncio.sleep(0))

        with pytest.raises(ValueError):
            loop.run_until_complete(monitor.start())


@pytest.mark.skipif(sys.version_info < (3, 8), reason='requires python3.8 or higher')
def test_can_configure_task_name() -> None:
    with with_event_loop() as loop:  # type: asyncio.AbstractEventLoop
        monitor = loopmon.create(loop, name='loopmon_task')
        tasks = asyncio.all_tasks(loop)
        assert any(t.get_name() == monitor.name for t in tasks)


def test_can_stop_running_monitor() -> None:
    with with_event_loop() as loop:  # type: asyncio.AbstractEventLoop
        monitor = loopmon.create(loop, name='loopmon_task')
        # Give loop time to run loopmon
        loop.run_until_complete(asyncio.sleep(0))
        assert monitor.running

        loop.run_until_complete(monitor.stop())
        assert not monitor.running
        # Give loop time to stop loopmon
        loop.run_until_complete(asyncio.sleep(0.1))

        tasks = asyncio.all_tasks(loop)
        assert not any(t.get_name() == monitor.name for t in tasks)


def test_can_detect_lag_of_another_thread(mocker: MockerFixture) -> None:
    delay_sec = 1
    interval = 0.1

    def body_of_another_thread(mon: loopmon.EventLoopMonitor) -> None:
        async def _inner() -> None:
            mon.install_to_loop()
            await asyncio.sleep(0)
            assert mon.running

            # block this thread -> `mon` must not collect during this blocking
            time.sleep(delay_sec)

            # Give mon time to collect lag
            await asyncio.sleep(interval / 2)
            await mon.stop()
            assert not mon.running

        asyncio.run(_inner())

    with with_event_loop() as loop:  # type: asyncio.AbstractEventLoop
        mock_of_main_thread = mocker.AsyncMock()
        monitor_of_main_thread = loopmon.create(loop, interval=interval, callbacks=(mock_of_main_thread,))
        # Give loop time to run loopmon
        loop.run_until_complete(asyncio.sleep(0))

        mock_of_another_thread = mocker.AsyncMock()
        monitor_of_another_thread = loopmon.SleepEventLoopMonitor(
            interval=interval,
            callbacks=(mock_of_another_thread,),
        )
        t = Thread(target=body_of_another_thread, args=(monitor_of_another_thread,))
        t.start()

        # this will block another thread and keep running main thread.
        # so `monitor_of_main_thread` will keep running without any lag,
        # but `monitor_of_main_thread` won't able to collect any data.
        loop.run_until_complete(loop.run_in_executor(None, t.join))
        loop.run_until_complete(asyncio.sleep(0))
        loop.run_until_complete(monitor_of_main_thread.stop())

        assert mock_of_main_thread.await_count == delay_sec / interval
        assert mock_of_another_thread.await_count == 1

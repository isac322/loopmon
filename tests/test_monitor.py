from __future__ import annotations

import asyncio

import loopmon


def test_can_catch_loop_close():
    loop = asyncio.new_event_loop()
    monitor = loopmon.create(loop)
    assert monitor.running
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()
    assert not monitor.running


def test_can_execute_callback(mocker):
    loop = asyncio.new_event_loop()
    mock = mocker.Mock()
    monitor = loopmon.create(loop, callbacks=(mock,))
    loop.run_until_complete(asyncio.sleep(0.1))
    mock.assert_called()


def test_can_detect_lag():
    loop = asyncio.new_event_loop()
    monitor = loopmon.create(loop)
    loop.run_until_complete(asyncio.sleep(1))

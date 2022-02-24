from __future__ import annotations

import sys

import pytest
from pytest_mock import MockerFixture, _util


@pytest.fixture(scope='function')
def mocker(pytestconfig, mocker) -> None:
    """python 3.7 does not contains AsyncMock"""
    if sys.version_info >= (3, 8):
        return mocker

    _util._mock_module = None
    overwritten = dict(mock_use_standalone_module=True)

    class Options:
        def getini(self, name):
            return overwritten.get(name, pytestconfig.getini(name))

        def override(self, name, value):
            overwritten[name] = value

    return MockerFixture(Options())

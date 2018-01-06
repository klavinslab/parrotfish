import json
import os
from pathlib import Path

import pytest

from parrotfish import ParrotFish
from parrotfish.session_environment import SessionManager
from parrotfish.utils.log import CustomLogging, logging


@pytest.fixture(scope="module")
def here():
    return os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="function")
def pfish(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp('env')
    session_manager = SessionManager(tmpdir)
    pfish = ParrotFish(session_manager)
    return pfish
#
#
# CustomLogging.set_level(logging.VERBOSE)

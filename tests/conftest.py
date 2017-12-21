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
def pfish(tmpdir):
    pfish = ParrotFish()
    sm = SessionManager()
    sm.metadata.set_dir(tmpdir)
    pfish.set_session_manager(sm)
    return pfish


CustomLogging.set_level(logging.VERBOSE)

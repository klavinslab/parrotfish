import json
import os
from pathlib import Path

import pytest

from parrotfish import *
from parrotfish.utils.log import CustomLogging, logging


@pytest.fixture(scope="module")
def set_session_environment():
    ParrotFish


@pytest.fixture(scope="module")
def config_path():
    folder = os.path.dirname(os.path.abspath(__file__))
    rel_loc = "secrets/config.json"
    return os.path.join(folder, rel_loc)


@pytest.fixture(scope="module")
def config():
    with open(os.path.abspath(config_path())) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def sessions():
    c = config()
    for name, session in c.items():
        ParrotFish.register(**session, session_name=name)

import json
import os
from pathlib import Path

import pytest

from parrotfish import *
from parrotfish.utils.log import CustomLogging, logging
from parrotfish.session_environment import env_data

@pytest.fixture(scope="module")
def here():
    return os.path.dirname(os.path.abspath(__file__))


env_data.env.name = "test_env.json"


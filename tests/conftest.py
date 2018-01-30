# import json
import os
# from pathlib import Path
#
import pytest

from parrotfish.core import CLI
from parrotfish.session_environment import SessionManager
import json
# from parrotfish import ParrotFish
# from parrotfish.session_environment import SessionManager
from parrotfish.utils.log import CustomLogging, logging
#
#
@pytest.fixture(scope="module")
def here():
    return os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="module")
def credentials(here):
    creds = {}
    with open(os.path.join(here, 'secrets/config.json')) as f:
        creds = json.load(f)
        for key, val in creds.items():
            val['name'] = key
    return creds


# @pytest.fixture(scope="function")
# def session_env(tmpdir_factory):

@pytest.fixture(scope="function")
def sm(tmpdir_factory):
    """Creates a new :class:`SessionManager` with its own temporary directories"""
    fishtank_loc = tmpdir_factory.mktemp('fishtankdir')
    env_loc = tmpdir_factory.mktemp('env')
    sm = SessionManager(fishtank_loc, meta_dir=env_loc, meta_name='temp_env.json')
    return sm


@pytest.fixture(scope="function")
def cli(sm):
    """Creates a new :class:`CLI` instance with its own temporary directories"""
    return CLI(sm)

CustomLogging.set_level(logging.VERBOSE)

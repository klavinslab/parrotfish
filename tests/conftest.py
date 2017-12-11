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


@pytest.fixture(scope="session")
def testing_environments():
    environments_dir = Path(Path(__file__).parent, 'environments').absolute()
    env1 = Path(environments_dir, 'env1')
    if not env1.is_dir():
        os.mkdir(str(env1))
    env2 = Path(environments_dir, 'env2')
    if not env2.is_dir():
        os.mkdir(str(env2))

    return env1, env2

@pytest.fixture(scope="function")
def reset():
    def wrapped():
        CustomLogging.set_level(logging.VERBOSE)
        Environment().environment_name = "test_env.pkl"
        if Environment().env_pkl().is_file():
            os.remove(Environment().env_pkl().absolute())
        try:
            ParrotFish.set_category("ParrotFishTest")
        except:
            pass
        env1, env2 = testing_environments()
        Environment().repo.set_dir(env1)
        Environment().repo.rmdirs()
        Environment().save()
    return wrapped


####### Setup test environment #######
reset()()
sessions()

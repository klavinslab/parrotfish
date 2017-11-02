import pytest
import os
import json
from parrotfish import *

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

@pytest.fixture(scope="function")
def reset():
    CustomLogging.set_level(logging.VERBOSE)
    Environment().environment_name = "test_env.pkl"
    if Environment().env_pkl().is_file():
        os.remove(Environment().env_pkl().absolute())
    ParrotFish.set_category("ParrotFishTest")

    environments_dir = Path(Path(__file__).parent, 'environments').absolute()

    Environment().repo.set_dir(environments_dir)
    Environment().repo.rmdirs()
    Environment().save()

####### Setup test environment #######
reset()
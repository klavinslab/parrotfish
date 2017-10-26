import pytest
import os
import json
from parrotfish import *

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
        ParrotFishSession.register(**session, session_name=name)

@pytest.fixture(scope="module")
def session_environments():
    session_environment = Path(__file__).resolve().parent.joinpath('session_environments')
    session_environment.mkdir(exist_ok=True)
    env1 = Path(session_environment, 'env1')
    env2 = Path(session_environment, 'env2')
    env1.mkdir(exist_ok=True)
    env2.mkdir(exist_ok=True)
    return env1, env2

@pytest.fixture(scope="module")
def reset_all():
    ParrotFishSession.reset(force=True)
    ParrotFishSession.set_remote(session_environments()[0])

@pytest.fixture(scope="function")
def register(config):
    reset_all()
    call_command("reset", force=True)
    for session_name, session_config in config.items():
        args = [session_config[x] for x in ["login", "password", "aquarium_url"]]
        call_command("register", *args, session_name=session_name)
        call_command("register", *args, session_name=session_name)
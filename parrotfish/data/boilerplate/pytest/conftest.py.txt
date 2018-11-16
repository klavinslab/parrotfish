import os
from parrotfish.session_environment import SessionManager
from parrotfish.core import CLI, open_from_local
import pytest


@pytest.fixture(scope="module")
def root_dir():
    testing_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(testing_dir)


@pytest.fixture(scope="module")
def cli(root_dir):
    cli_inst = open_from_local(os.path.join(root_dir, '..')))
    return cli_inst

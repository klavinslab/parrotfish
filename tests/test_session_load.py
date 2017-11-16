import pytest
from parrotfish import *


def test_session_load(sessions, config):

    for name, session_info in config.items():
        Environment().session_manager.set_current(name)

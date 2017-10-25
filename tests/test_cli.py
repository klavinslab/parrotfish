import pytest
from parrotfish import *

@pytest.fixture(scope="function")
def register():
    pseudo_cli("reset", force=True)
    pseudo_cli("register", "vrana", "Mountain5", "http://52.27.43.242:81", session_name="nursery")
    pseudo_cli("register", "vrana", "Mountain5", "http://52.27.43.242", session_name="production")

def test_registration(register):
    assert Session.session_name() == "production"

def test_checkout():
    pseudo_cli("checkout", "nursery")
    assert Session.session_name() == "nursery"

    pseudo_cli("checkout", "production")
    assert Session.session_name() == "production"

def test_clear(register):
    pseudo_cli("reset", force=True)
    assert Session.empty()
    assert Session.session is None

    pseudo_cli("register", "vrana", "Mountain5", "http://52.27.43.242", session_name="production")
    assert Session.session is not None

def test_fetch(register):
    pseudo_cli("checkout", "nursery")
    pseudo_cli("set_category", "Justin")
    pseudo_cli("fetch")
    assert os.path.isdir(ParrotFishSession.getcategorydir())

def test_pull():
    raise NotImplementedError()

def test_push():
    raise NotImplementedError()


import pytest

SESSION_NAME = "nursery"

@pytest.fixture(scope="module")
def session(cli):
    return cli._session_manager.get_session(SESSION_NAME)
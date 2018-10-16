from parrotfish.session_environment import SessionEnvironment
from pydent import AqSession
from cryptography.fernet import Fernet


def test_create_boilerplate_test_code_from_session_env(tmpdir, credentials):
    """This test creates an session_environment and writes an Library.
    It then reads it. Its expected the loaded Library and Library
    retrieved from the AqSession will have equivalent attributes."""
    session = AqSession(**credentials['nursery'])
    session_env = SessionEnvironment(**credentials['nursery'], encryption_key=Fernet.generate_key())

    session_env.create_pytest_boilerplate(session)

# def test_boilerplate_from_cli(cli, credentials):
#     cli.register(**credentials['nursery'])
#     cli.create_pytest_boilerplate(cli.current_session)
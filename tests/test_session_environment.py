from parrotfish.session_environment import SessionEnvironment, SessionManager
from pydent import AqSession
import os
from cryptography.fernet import Fernet

def test_operation_type_controller(tmpdir, credentials):
    """This test creates an session_environment and writes an OperationType.
    It then reads it. Its expected the loaded OperationType and OperationType
    retrieved from the AqSession will have equivalent attributes."""
    session = AqSession(**credentials['nursery'])
    ot = session.OperationType.all()[-1]

    session_env = SessionEnvironment(**credentials['nursery'], encryption_key=Fernet.generate_key())
    session_env.set_dir(tmpdir)

    session_env.write_operation_type(ot)

    loaded_ot = session_env.read_operation_type(ot.category, ot.name)

    assert loaded_ot.dump() == ot.dump()
    assert loaded_ot.protocol.dump() == ot.protocol.dump()
    assert loaded_ot.precondition.dump() == ot.precondition.dump()
    assert loaded_ot.documentation.dump() == ot.documentation.dump()
    assert loaded_ot.cost_model.dump() == ot.cost_model.dump()


def test_library_controller(tmpdir, credentials):
    """This test creates an session_environment and writes an Library.
    It then reads it. Its expected the loaded Library and Library
    retrieved from the AqSession will have equivalent attributes."""
    session = AqSession(**credentials['nursery'])
    lib = session.Library.all()[-1]

    session_env = SessionEnvironment(**credentials['nursery'], encryption_key=Fernet.generate_key())
    session_env.set_dir(tmpdir)

    session_env.write_library(lib)

    loaded_lib = session_env.read_library_type(lib.category, lib.name)

    assert loaded_lib.dump() == lib.dump()
    assert loaded_lib.source.dump() == loaded_lib.source.dump()


def test_session_manager_register(sm, credentials):
    """This tests that register session will """
    assert not hasattr(sm, "nursery")
    sm.register_session(**credentials['nursery'])
    assert hasattr(sm, "nursery")

    session = sm.get_session("nursery")
    assert session.name == credentials['nursery']['name']
    assert session.login == credentials['nursery']['login']
    assert session.url == credentials['nursery']['aquarium_url']


def test_session_manager_set_current(sm, credentials):
    sm.register_session(**credentials['nursery'])
    sm.register_session(**credentials['production'])
    assert sm.current_session is None

    # set to nursery
    sm.set_current("nursery")
    assert sm.current_session.name == "nursery"

    # set to production
    sm.set_current("production")
    assert sm.current_session.name == "production"

    # set to doesnt exit
    sm.set_current("doesn't exist")
    assert sm.current_session.name == "production"


def test_session_manage_mkdirs(sm, credentials):
    """This tests to ensure the directories are created as expected"""
    sm.register_session(**credentials['nursery'])
    sm.register_session(**credentials['production'])

    g = sm.abspaths
    sm.mkdirs()

    assert os.path.isdir(os.path.join(sm.abspath, "nursery", "protocols"))
    assert os.path.isdir(os.path.join(sm.abspath, "production", "protocols"))
    print()
    print(sm.show(print_files=True))

    sm.rmdirs()
    assert not os.path.isdir(sm.abspath)

# TODO: better test for loaded_sm
def test_session_manager_save_and_load(sm, credentials):

    sm.register_session(**credentials['nursery'])
    sm.register_session(**credentials['production'])

    sm.save()

    copied_sm = SessionManager(sm.abspath, meta_dir=sm.metadata.abspath, meta_name=sm.metadata.env.name)
    copied_sm.load()
    assert len(copied_sm._children) == len(sm._children)
    assert copied_sm.sessions.keys() == sm.sessions.keys()
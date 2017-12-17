from parrotfish.session_environment import SessionEnvironment, SessionManager
from pydent import AqSession
import os


def test_operation_type_controller():
    """This test creates an session_environment and writes an OperationType.
    It then reads it. Its expected the loaded OperationType and OperationType
    retrieved from the AqSession will have equivalent attributes."""
    session = AqSession('vrana', 'Mountain5', 'http://52.27.43.242:81/')
    ot = session.OperationType.all()[-1]

    session_env = SessionEnvironment('mysession', session)

    session_env.write_operation_type(ot)

    loaded_ot = session_env.read_operation_type(ot.category, ot.name)

    assert loaded_ot.dump() == ot.dump()
    assert loaded_ot.protocol.dump() == ot.protocol.dump()
    assert loaded_ot.precondition.dump() == ot.precondition.dump()
    assert loaded_ot.documentation.dump() == ot.documentation.dump()
    assert loaded_ot.cost_model.dump() == ot.cost_model.dump()


def test_library_controller():
    """This test creates an session_environment and writes an Library.
    It then reads it. Its expected the loaded Library and Library
    retrieved from the AqSession will have equivalent attributes."""
    session = AqSession('vrana', 'Mountain5', 'http://52.27.43.242:81/')
    lib = session.Library.all()[-1]

    session_env = SessionEnvironment('mysession', session)

    session_env.write_library(lib)

    loaded_lib = session_env.read_library_type(lib.category, lib.name)

    assert loaded_lib.dump() == lib.dump()
    assert loaded_lib.source.dump() == loaded_lib.source.dump()


def test_session_manager_register():
    """This tests that register session will """
    env = SessionManager()

    assert not hasattr(env, "nursery")
    env.register_session("vrana", "Mountain5", 'http://52.27.43.242:81/', "nursery")
    assert hasattr(env, "nursery")

    session = env.get_session("nursery")
    assert session.name == "nursery"
    assert session.login == "vrana"
    assert session.url == 'http://52.27.43.242:81/'


def test_session_manager_set_current():
    env = SessionManager()
    env.register_session("vrana", "Mountain5", 'http://52.27.43.242:81/', "nursery")
    env.register_session("vrana", "Mountain5", 'http://52.27.43.242:81/', "production")
    assert env.current is None

    # set to nursery
    env.set_current("nursery")
    assert env.current.name == "nursery"

    # set to production
    env.set_current("production")
    assert env.current.name == "production"

    # set to doesnt exit
    env.set_current("doesn't exist")
    assert env.current.name == "production"


def test_session_manage_mkdirs(tmpdir):
    """This tests to ensure the directories are created as expected"""
    env = SessionManager()
    env.register_session("vrana", "Mountain5", 'http://52.27.43.242:81/', "nursery")
    env.register_session("vrana", "Mountain5", 'http://52.27.43.242:81/', "production")

    env.set_dir(tmpdir)
    g = env.abspaths
    env.mkdirs()

    assert os.path.isdir(os.path.join(tmpdir, env.name, "nursery", "protocols"))
    assert os.path.isdir(os.path.join(tmpdir, env.name, "production", "protocols"))
    print()
    print(env.show(print_files=True))

    env.rmdirs()
    assert not os.path.isdir(os.path.join(tmpdir, env.name))


def test_session_manager_save_and_load_environments(tmpdir):

    sm1 = SessionManager()
    sm1.set_dir(tmpdir)
    sm1.register_session("vrana", "Mountain5", 'http://52.27.43.242:81/', "nursery")
    sm1.register_session("vrana", "Mountain5", 'http://52.27.43.242:81/', "production")
    sm1.set_dir(tmpdir)

    sm1.save_environments()
    sm2 = SessionManager.load_environments(os.path.join(tmpdir, sm1.name))

    assert hasattr(sm2, "nursery")
    assert hasattr(sm2, "production")


def test_session_manager_save_and_load():

    sm1 = SessionManager()
    sm1.set_dir('.')
    sm1.register_session("vrana", "Mountain5", 'http://52.27.43.242:81/', "nursery")
    sm1.register_session("vrana", "Mountain5", 'http://52.27.43.242:81/', "production")
    sm1.set_dir('.')

    sm1.save()

    sm2 = SessionManager.load()
    pass
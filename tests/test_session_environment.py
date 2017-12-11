from parrotfish.session_environment import SessionEnvironment
from pydent import AqSession

def test_operation_type_controller():
    session = AqSession('vrana', 'Mountain5', 'http://52.27.43.242:81/')
    ot = session.OperationType.all()[-1]

    session_env = SessionEnvironment('mysession')

    session_env.write_operation_type(ot)

    loaded_ot = session_env.read_operation_type(ot.category, ot.name)
    print(loaded_ot)

    session_env.save()


def test_library_controller():
    session = AqSession('vrana', 'Mountain5', 'http://52.27.43.242:81/')
    lib = session.Library.all()[-1]

    session_env = SessionEnvironment('mysession')

    session_env.write_library(lib)

    loaded_lib = session_env.read_library_type(lib.category, lib.name)
    print(loaded_lib)

"""Tests core command line interface"""

from parrotfish.core import CLI
from parrotfish import utils
from parrotfish.session_environment import SessionManager
import os
from pydent import AqSession
import uuid


login = "vrana"
password = "Mountain5"
url = "http://52.27.43.242:81/"
OT_TEST_CATEGORY = "ParrotFishTest"



def test_register(cli, credentials):
    assert len(cli.sessions) == 0
    cli.register(**credentials['nursery'])
    assert len(cli.sessions) == 1

    # add another session
    cli.register(**credentials['nursery2'])
    assert len(cli.sessions) == 2


def test_register_with_same_name(cli, credentials):
    assert len(cli.sessions) == 0
    cli.register(**credentials['nursery'])
    assert len(cli.sessions) == 1

    # register with same name
    cli.register(**credentials['nursery'])
    assert len(cli.sessions) == 1


def test_unregister(cli):
    assert len(cli.sessions) == 0
    cli.register(login, password, url, "nursery")
    assert len(cli.sessions) == 1

    cli.unregister("nursery")
    assert len(cli.sessions) == 0


def test_load(cli, credentials):
    assert len(cli.sessions) == 0
    cli.register(**credentials['nursery'])
    cli._save()

    # load another cli using same files
    old_sm = cli._session_manager
    copied_sm = SessionManager(old_sm.abspath, config_dir=old_sm.config.abspath, config_name=old_sm.config.env_settings.name)
    copied_sm.load()
    cli2 = CLI(copied_sm)

    assert len(cli.sessions) == 1
    assert len(cli2.sessions) == 1


def test_set_current(cli, credentials):
    assert len(cli.sessions) == 0
    cli.register(**credentials['nursery'])
    assert len(cli.sessions) == 1
    assert cli._session_manager.current_session.name == 'nursery'

    # add another session
    cli.register(**credentials['nursery2'])
    assert len(cli.sessions) == 2
    assert cli._session_manager.current_session.name == 'nursery2'

    # switch to nursery
    cli.set_session("nursery")
    assert cli._session_manager.current_session.name == "nursery"

    # switch to non-existent session
    cli.set_session("does not exist")


def test_move_repo(cli, tmpdir_factory, credentials):
    newdir = tmpdir_factory.mktemp('new_dir')

    # register and move repo
    cli.register(**credentials['nursery'])

    # assert root directory
    old_root = cli._session_manager._SessionManager__config['root']

    # move the repo
    cli.move_repo(newdir)

    # add some random file
    cli._session_manager.add_file("newfile.txt", attr="newfile")
    cli._session_manager.get("newfile").write("something")
    assert os.path.exists(os.path.join(cli._session_manager.abspath, "newfile.txt"))

    # assert path of session_manager moved
    assert str(cli._session_manager.abspath) == os.path.join(str(newdir), cli._session_manager.name)

    # assert root in env.json was changed
    new_root = cli._session_manager._SessionManager__config['root']
    assert new_root == os.path.join(str(newdir), cli._session_manager.name)
    assert old_root != new_root

    # ensure file moved along with repo move
    assert os.path.exists(os.path.join(newdir, cli._session_manager.name, "newfile.txt"))


def test_categories(cli, credentials):
    cli.register(**credentials['nursery'])
    categories = cli._get_categories()
    assert len(categories) > 0

    cli.categories()


def test_list_protocols(cli, credentials):
    cli.register(**credentials['nursery'])
    cli.fetch(OT_TEST_CATEGORY)
    cli.protocols()


def test_fetch(cli, credentials):
    cli.register(**credentials['nursery'])
    cli.fetch(OT_TEST_CATEGORY)
    cli.ls()

    sm = cli._session_manager

    # get first session folder
    session = sm.list_dirs()[0]

    categories = session.categories
    assert OT_TEST_CATEGORY in [x.name for x in categories]

    # files
    for cat in categories:
        protocols = cat.list_dirs()
        for protocol in protocols:
            files = protocol.list_files()
            assert len(files) > 0


def test_push_category(cli, credentials):
    cli.register(**credentials['nursery'])
    cli.fetch(OT_TEST_CATEGORY)
    cli.ls()

    # just get the first operation type
    sm = cli._session_manager
    session = sm.list_dirs()[0]

    ot_name = "ParrotFishPushPullOperation"
    dirs = session.categories[0].list_dirs()
    protocol = None
    for d in dirs:
        if d.name == ot_name:
            protocol = d

    old_local_ot = session.read_operation_type(OT_TEST_CATEGORY, protocol.name)
    aqsession = AqSession(**credentials['nursery'])
    old_loaded_ot = aqsession.OperationType.find_by_name(old_local_ot.name)

    # push the content
    new_content = str(uuid.uuid4())
    protocol.protocol.write(new_content)
    cli.push(OT_TEST_CATEGORY)

    # new operation types
    new_local_ot = session.read_operation_type(OT_TEST_CATEGORY, protocol.name)
    new_loaded_ot = aqsession.OperationType.find_by_name(new_local_ot.name)

    # compare content
    assert new_loaded_ot.protocol.content == new_content
    assert new_local_ot.protocol.content == new_content
    assert old_local_ot.protocol.content != new_content
    print(utils.compare_content(old_local_ot.protocol.content, new_local_ot.protocol.content))


def test_run_test_for_single_operation_type(cli, credentials):
    cli.register(**credentials['nursery'])
    cli.fetch(OT_TEST_CATEGORY)
    result = cli.run_test(OT_TEST_CATEGORY, "ParrotFishTestOperation", 5, True)
    print(result)


def test_run_test_for_category(cli, credentials):
    cli.register(**credentials['nursery'])
    cli.fetch(OT_TEST_CATEGORY)
    results = cli.run_tests(OT_TEST_CATEGORY, 5, True)
    for k, v in results.items():
        print("{}: {}".format(k, v['passed']))
    # cli.register(**credentials['nursery'])
    # cli.fetch(OT_TEST_CATEGORY)
    # cli.ls()
    #
    # sm = cli._session_manager

    # # get first session folder
    # session = sm.list_dirs()[0]
    #
    # categories = session.categories
    # assert OT_TEST_CATEGORY in [x.name for x in categories]
    #
    # # files
    # for cat in categories:
    #     protocols = cat.list_dirs()
    #     for protocol in protocols:
    #         files = protocol.list_files()
    #         assert len(files) > 0
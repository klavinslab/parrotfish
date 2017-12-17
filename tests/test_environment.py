from parrotfish import *
from pathlib import Path
import os


def test_env_borg():

    env = Environment()

    env2 = Environment()

    env.name = "AAA"
    env2.name = "BBB"
    assert env.name == "BBB"
    assert env2.name == "BBB"


def test_env_pkl_path():

    env = Environment()

    this_dir = Path(Path(__file__).absolute().parent.parent,
                    'parrotfish', '.environ')
    assert env.env_pkl().parent == this_dir


def test_env_paths(sessions, reset):

    env = Environment()
    s = env.session_manager.set_current
    env.session_manager.set_current('nursery')
    assert env.session_dir().relpath == Path(env.repo.name, 'protocols', 'nursery')

    assert env.get_category('cat1').relpath == Path(
        env.repo.name, 'protocols', 'nursery', 'cat1')
    assert env.get_category('cat2').relpath == Path(
        env.repo.name, 'protocols', 'nursery', 'cat2')

    env.session_manager.set_current('production')
    assert env.session_dir().relpath == Path(
        env.repo.name, 'protocols', 'production')
    assert env.get_category('cat1').relpath == Path(
        env.repo.name, 'protocols', 'production', 'cat1')
    assert env.get_category('cat2').relpath == Path(
        env.repo.name, 'protocols', 'production', 'cat2')

    pkg_dir = Path(__file__).absolute().parent.parent
    new_dir = Path(pkg_dir, 'tests', 'environments')
    env.repo.set_dir(new_dir)
    assert env.session_dir().relpath == Path(
        env.repo.name, 'protocols', 'production')
    assert env.get_category('cat1').abspath == Path(
        new_dir, env.repo.name, 'protocols', 'production', 'cat1')
    assert env.get_category('cat2').abspath == Path(
        new_dir, env.repo.name, 'protocols', 'production', 'cat2')
    reset()

# # TODO: better info test
# def test_env_info(sessions):
#
#     env = Environment()
#
#     info = env.info()
#
#     assert info['parent_dir'] == env.dir
#     assert info['sessions'] == AqSession().sessions
#     assert info['session_name'] == AqSession().session_name
#     assert info['category'] == env.category


def test_env_save_and_load(config):
    # Setup environment
    e = Environment()
    e.session_manager.create_from_json(config)

    e.session_manager.set_current('production')
    e.category = "cat1"

    # remove env_pkl
    pkg_dir = Path(__file__).absolute().parent.parent
    env = Path(pkg_dir, 'parrotfish', '.environ',
               Environment().environment_name)
    if env.is_file():
        os.remove(env)
    assert not env.is_file()

    # save environment
    Environment().save()

    # assert file was created
    assert env.is_file()

    # assert BEFORE loading
    assert e.session_manager.session_name == "production"
    assert e.category == "cat1"

    e.session_manager.set_current("nursery")
    e.category = "cat2"

    assert e.session_manager.session_name == "nursery"
    assert e.category == "cat2"

    e.load()

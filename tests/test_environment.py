from parrotfish import *

def test_env_borg(sessions):

    env = Environment()

    env2 = Environment()

    env.name = "AAA"
    env2.name = "BBB"
    assert env.name == "BBB"
    assert env2.name == "BBB"

def test_env_pkl_path():

    env = Environment()

    this_dir = Path(Path(__file__).absolute().parent.parent, '.environ')
    assert env.env_pkl().parent == this_dir

def test_env_paths(sessions, reset):

    env = Environment()

    env.session.set('nursery')
    assert env.session_dir().relpath == Path(env.repo.name, 'protocols', 'nursery')

    assert env.get_category('cat1').relpath == Path(env.repo.name, 'protocols', 'nursery', 'cat1')
    assert env.get_category('cat2').relpath == Path(env.repo.name, 'protocols', 'nursery', 'cat2')

    env.session.set('production')
    assert env.session_dir().relpath == Path(env.repo.name, 'protocols', 'production')
    assert env.get_category('cat1').relpath == Path(env.repo.name, 'protocols', 'production', 'cat1')
    assert env.get_category('cat2').relpath == Path(env.repo.name, 'protocols', 'production', 'cat2')

    pkg_dir = Path(__file__).absolute().parent.parent
    new_dir = Path(pkg_dir, 'tests', 'environments')
    env.repo.set_dir(new_dir)
    assert env.session_dir().relpath == Path(env.repo.name, 'protocols', 'production')
    assert env.get_category('cat1').abspath == Path(new_dir, env.repo.name, 'protocols', 'production', 'cat1')
    assert env.get_category('cat2').abspath == Path(new_dir, env.repo.name, 'protocols', 'production', 'cat2')
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
    e.session.create_from_json(config)

    e.session.set('production')
    e.category = "cat1"

    # remove env_pkl
    pkg_dir = Path(__file__).absolute().parent.parent
    env = Path(pkg_dir, '.environ', Environment().environment_name)
    if env.is_file():
        os.remove(env)
    assert not env.is_file()

    # save environment
    Environment().save()

    # assert file was created
    assert env.is_file()

    # assert BEFORE loading
    assert e.session.session_name == "production"
    assert e.category == "cat1"

    e.session.set("nursery")
    e.category = "cat2"

    assert e.session.session_name == "nursery"
    assert e.category == "cat2"

    e.load()






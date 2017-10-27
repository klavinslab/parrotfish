from pathlib import Path
from pydent import Session
import shutil

# Globals
class DN(object):
    """ Directory names """
    MODULE = Path(__file__).parent.parent.resolve()
    ROOT = 'fishtank'
    MASTER = "protocols"
    DEFAULT_ENV = "default_env.pkl"
    CODE_PKL = "code.pkl"
    ENV_DIR = Path(MODULE, '.environ').resolve()

# TODO: rename bin to root
class EnvironmentManager(type):
    _root_location = Path(DN.MODULE, DN.ROOT).resolve()
    _curr_env = DN.DEFAULT_ENV

    def build_path(cls, *paths):
        path = Path.joinpath(*paths)
        while not path.is_dir():
            path.resolve().mkdir(exist_ok=True)
        return path.resolve()

    @property
    def root(cls):
        return cls.build_path(cls._root_location)

    def copy_root(cls, new_path):
        if not new_path.exists():
            shutil.copytree(cls.root, new_path)

    def set_root(cls, new_path):
        if not new_path.parent.is_dir():
            raise Exception("Cannot set_root. Directory \"{}\" does not exist.".format(new_path.parent))
        cls._root_location = cls.build_path(new_path)

    @property
    def master_dir(cls):
        return cls.build_path(cls._root_location, DN.MASTER)

    @property
    def session_dir(cls):
        return cls.build_path(cls.master_dir, Session.session_name)

    def category_dir(cls, cat):
        return cls.build_path(cls.session_dir, cat)

    @property
    def categories(cls):
        return [x for x in list(cls.session_dir.iterdir()) if x.is_dir()]

    @property
    def env(cls):
        return cls.build_path(DN.ENV_DIR).joinpath(Path(cls._curr_env))

    @property
    def code_pickle(cls):
        return Path(cls.session_dir, DN.CODE_PKL)


class Environment(object, metaclass=EnvironmentManager):

    def list_env(cls):
        return list(DN.ENV_DIR.glob("*"))

    @staticmethod
    def set_env(env_name):
        Environment._curr_env = env_name

    @staticmethod
    def default_env():
        Environment.set_env(EnvironmentManager._curr_env)
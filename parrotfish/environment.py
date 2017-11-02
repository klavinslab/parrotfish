from pydent import AqSession
from .utils import *
from magicdir import *
import dill
from .log import *
import os

logger = CustomLogging.get_logger(__name__)


class Environment(object):
    """ Manages the Aquarium session """
    _shared_state = {}
    ALL = "all"

    def __init__(self):
        self.__dict__ = self._shared_state
        if self._shared_state == {}:
            self.repo = MagicDir('fishtank')
            self.repo.add('protocols')
            self.category = None
            self.environment_name = 'default_env.pkl'
            self.session = AqSession()

    def pkg_dir(self):
        return Path(__file__).parent.parent.absolute()

    def session_dir(self):
        return self.repo.protocols.add(self.session.session_name, push_up=False, make_attr=False)

    def get_category(self, cat):
        if os.sep in cat:
            new_cat = sanitize_filename(cat)
            logger.warning("Category {} is not a valid name. Renamed to {}".format(cat, new_cat))
            cat = new_cat
        return self.session_dir().add(cat, push_up=False, make_attr=False)

    def code_pkl(self):
        return self.session_dir().add_file('code.pkl', attr='codepkl', push_up=False)

    def env_pkl(self):
        e = Path(self.pkg_dir(), '.environ')
        os.makedirs(e, exist_ok=True)
        return Path(e, self.environment_name)

    def move_repo(self, new_parent):
        self.repo.mvdirs(new_parent)

    def save(self):
        with open(self.env_pkl(), 'wb') as f:
            dill.dump(self, f)

    def load(self):
        with open(self.env_pkl(), 'rb') as f:
            dill.load(f)

    def use_all_categories(self):
        return self.category is None or \
               self.category.lower().strip() == Environment.ALL

    def __setstate__(self, state):
        """ Override so that sessions can be updated with pickle.load """
        self.__class__._shared_state.update(state)
        self.__dict__ = self.__class__._shared_state

    # def info(self):
    #     return {
    #         "sessions": AqSession().sessions,
    #         "session_name": AqSession().session_name,
    #         "parent_dir": str(self.dir),
    #         "category": self.category
    #     }

    # def save(self):
    #     with self.get_env.open('wb') as f:
    #         dill.dump(self.info(), f)
    #
    # def load(self):
    #     if not self.get_env().is_file():
    #         logger.warning("environment file {} not found".format(str(self.get_env())))
    #         return None
    #     with self.get_env.open('rb') as f:
    #         loaded = dill.load(f)
    #         session_name = loaded['session_name']
    #         sessions = loaded['sessions']
    #         parent_dir = Path(loaded['parent_dir']).absolute()
    #         if not parent_dir.is_dir():
    #             logger.error("parent_directory {} does not exist".format(parent_dir))
    #         self.set_dir()
    #         category = loaded['category']
    #
    #         if session_name not in sessions:
    #             logger.warning("session {} not found in sessions {}")
    #         else:
    #             AqSession().set(session_name)
    #
    #         self.category = category
    #
    #         logger.verbose("environment loaded from {}".format(str(self.get_env)))
    #         return loaded


#
#
# # Globals
# class DN(object):
#     """ Directory names """
#     MODULE = Path(__file__).parent.parent.resolve()
#     ROOT = 'fishtank'
#     MASTER = "protocols"
#     DEFAULT_ENV = "default_env.pkl"
#     CODE_PKL = "code.pkl"
#     ENV_DIR = Path(MODULE, '.environ').resolve()
#
# # TODO: rename bin to root
# class EnvironmentManager(type):
#     _root_location = Path(DN.MODULE, DN.ROOT).resolve()
#     _curr_env = DN.DEFAULT_ENV
#
#     def build_path(cls, *paths):
#         path = Path.joinpath(*paths)
#         while not path.is_dir():
#             path.resolve().mkdir(exist_ok=True)
#         return path.resolve()
#
#     @property
#     def root(cls):
#         root_path = Path(cls._root_location)
#         os.makedirs(root_path, exist_ok=True)
#         return root_path
#
#     def copy_root(cls, new_path):
#         if not new_path.exists():
#             shutil.copytree(cls.root, new_path)
#
#     def set_root(cls, new_path):
#         if not new_path.parent.is_dir():
#             raise Exception("Cannot set_root. Directory \"{}\" does not exist.".format(new_path.parent))
#         cls._root_location = cls.build_path(new_path)
#
#     @property
#     def master_dir(cls):
#         return cls.build_path(cls._root_location, DN.MASTER)
#
#     @property
#     def session_dir(cls):
#         return cls.build_path(cls.master_dir, Session.session_name)
#
#     def category_dir(cls, cat):
#         return cls.build_path(cls.session_dir, cat)
#
#     @property
#     def categories(cls):
#         return [x for x in list(cls.session_dir.iterdir()) if x.is_dir()]
#
#     @property
#     def env(cls):
#         return cls.build_path(DN.ENV_DIR).joinpath(Path(cls._curr_env))
#
#     @property
#     def code_pickle(cls):
#         return Path(cls.session_dir, DN.CODE_PKL)
#
#
# class Environment(object, metaclass=EnvironmentManager):
#
#     def list_env(cls):
#         return list(DN.ENV_DIR.glob("*"))
#
#     @staticmethod
#     def set_env(env_name):
#         Environment._curr_env = env_name
#
#     @staticmethod
#     def default_env():
#         Environment.set_env(EnvironmentManager._curr_env)
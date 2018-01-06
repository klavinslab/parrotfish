import os
import dill
from magicdir import MagicDir
from parrotfish.utils.log import CustomLogging
from parrotfish.utils import sanitize_filename, sanitize_attribute
from pydent.models import OperationType, Library
from pydent import AqSession
from glob import glob
import json
import datetime
from parrotfish.__version__ import __version__
logger = CustomLogging.get_logger(__name__)


# TODO: different name for ENV_DATA
# where saved data is stored
HERE = os.path.dirname(os.path.abspath(__file__))


class SessionEnvironment(MagicDir):
    """

    Example::

        SessionEnvironment1
           └──Category1
               |──OperationType1
               |   |──OperationType1.json
               |   |──OperationType1.rb
               |   |──OperationType1__cost_model.rb
               |   |──OperationType1__documentation.rb
               |   └──OperationType1__precondition.rb
               └──LibraryType1
                   |──LibraryType1.rb
                   └──LibraryType1.json

    """
    ENV_PKL = '.env_pkl'

    def __init__(self, name, session):
        """

        :param path: The path of this session
        :type path: str
        """
        super().__init__(name, push_up=False, check_attr=False)

        # set the session
        self.session = session

        # add the environment pickle
        self.add_file(self.ENV_PKL, attr='env_pkl')

        # add protocols directory
        self.add('protocols')

    def save_to_pkl(self):
        """Save to pickle"""
        with self.env_pkl.open('wb') as f:
            dill.dump(self, f)

    def reload_from_pkl(self):
        """Load attributes from the pickle"""
        with self.env_pkl.open('wb') as f:
            loaded = dill.load(f)
            vars(self).updated(vars(loaded))

    @classmethod
    def load_from_pkl(cls, env_pkl):
        """Load from pickle"""
        if os.path.isfile(env_pkl):
            with open(env_pkl, 'rb') as f:
                return dill.load(f)

    def get_category_dir(self, category):
        cat_dirname = sanitize_filename(category)
        cat_dir = self.protocols.add(sanitize_attribute(cat_dirname))
        return cat_dir

    @property
    def categories(self):
        """Return a list of categories (MagicDir)"""
        return self.protocols.list_dirs()

    # @property
    # def protocols(self, category):
    #     cat_dir = self.get_category_dir(category)
    #     return cat_dir.list_dirs()
    #
    # @property
    # def operation_types(self, category):
    #     protocols = self.protocols
    #     return [p for p in protocols if p.has("protocol")]
    #
    # @property
    # def libraries(self, category):
    #     protocols = self.protocols
    #     return [p for p in protocols if p.has("source")]

    # Methods for writing and reading OperationType and Library
    # TODO: library and operation type methods are pretty similar, we could generalize but there's only two different models...
    def get_operation_type_dir(self, category, operation_type_name):
        # add the category directory to the protocols directory
        cat_dir = self.get_category_dir(category)

        # add a new folder using operation type name
        basename = sanitize_filename(operation_type_name)
        ot_dir = cat_dir.add(basename)

        # add operation type files
        ot_dir.add_file('{}.json'.format(basename), attr='meta')
        ot_dir.add_file('{}.rb'.format(basename), attr='protocol')
        ot_dir.add_file('{}__precondition.rb'.format(basename), attr='precondition')
        ot_dir.add_file('{}__cost_model.rb'.format(basename), attr='cost_model')
        ot_dir.add_file('{}__documentation.rb'.format(basename), attr='documentation')

        return ot_dir

    def get_library_type_dir(self, category, library_name):
        # add the category directory to the protocols directory
        cat_dir = self.get_category_dir(category)

        # add a new folder using operation type name
        basename = sanitize_filename(library_name)
        lib_dir = cat_dir.add(basename)

        # add library source file
        lib_dir.add_file('{}.json'.format(basename), attr='meta')
        lib_dir.add_file('{}.rb'.format(basename), attr='source')

        return lib_dir

    def write_operation_type(self, operation_type):
        ot_dir = self.get_operation_type_dir(operation_type.category, operation_type.name)

        include = {
            'field_types': 'allowable_field_types'
        }

        metadata = operation_type.dump(
            include={'protocol': {},
                     'documentation': {},
                     'cost_model': {},
                     'precondition': {},
                     "field_types": "allowable_field_types"
                     }
            )

        # write metadata
        ot_dir.meta.dump_json(
            metadata,
            indent=4,
        )

        # write codes
        for accessor in ['protocol', 'precondition', 'documentation', 'cost_model']:
            logger.cli("    saving {}".format(accessor))
            ot_dir.get(accessor).write(metadata[accessor]['content'])

    def write_library(self, library):
        lib_dir = self.get_library_type_dir(library.category, library.name)

        # write json
        lib_dir.meta.dump_json(library.dump(include={'source'}), indent=4)

        # write codes
        lib_dir.source.write(library.code('source').content)

    def read_operation_type(self, category, name):
        ot_dir = self.get_operation_type_dir(category, name)
        metadata = ot_dir.meta.load_json()  # load the meta data from the .json file
        ot = OperationType.load(metadata)

        ot.protocol.content = ot_dir.protocol.read()
        ot.precondition.content = ot_dir.precondition.read()
        ot.documentation.content = ot_dir.documentation.read()
        ot.cost_model.content = ot_dir.cost_model.read()
        ot.connect_to_session(self.session)
        return ot

    def read_library_type(self, category, name):
        lib_dir = self.get_library_type_dir(category, name)
        metadata = lib_dir.meta.load_json()
        lib = Library.load(metadata)

        lib.source.content = lib_dir.source.read()
        lib.connect_to_session(self.session)
        return lib


class SessionManager(MagicDir):
    """
    SessionManager reads and writes `:class:OperationType` and `:class:Library.`
    The path of the directory (*SessionManagerName*) is saved in
    *meta_dir/environment_data/meta_name.json* in *root*.

    Example session structure::

        meta_dir
        └──environment_data
            └──meta_name.json

        SessionManagerName
        |──SessionEnvironment1
        |   └──Category1
        |       |──OperationType1
        |       |   |──OperationType1.json
        |       |   |──OperationType1.rb
        |       |   |──OperationType1__cost_model.rb
        |       |   |──OperationType1__documentation.rb
        |       |   └──OperationType1__precondition.rb
        |       └──LibraryType1
        |           |──LibraryType1.rb
        |           └──LibraryType1.json
        └──SessionEnvironment2
            └── ...
    """

    DEFAULT_METADATA_LOC = os.path.join(HERE, 'environment_data')
    DEFAULT_METADATA_NAME = 'env.json'

    def __init__(self, dir, name="FishTank", meta_dir=None, meta_name=None):
        """
        SessionManager constructor

        :param dir: directory
        :type dir: str
        :param name: name of the folder
        :type name: str
        :param meta_dir: directory to store the metadata
        :type meta_dir: str
        :param meta_name: name of the file to store the metadata
        :type meta_name: str
        """
        super().__init__(name, push_up=False, check_attr=False)
        self.set_dir(dir)

        # Add metadata
        # this is where session manager information will be stored
        if meta_dir is None:
            meta_dir = self.DEFAULT_METADATA_LOC
        if meta_name is None:
            meta_name = self.DEFAULT_METADATA_NAME
        self.metadata = MagicDir(meta_dir)
        self.metadata.add_file(meta_name, 'env')

        self._current_session = None

    def register_session(self, login, password, aquarium_url, name):
        """Registers a new session by creating a AqSession, creating
        a SessionEnvironment and adding it to the SessionManager"""
        if name in self.sessions:
            logger.warning("'{}' already exists!".format(name))
            return
        session = AqSession(login, password, aquarium_url, name=name)
        session_env = SessionEnvironment(name, session)
        self._add_session_env(session_env)

    def remove_session(self, name):
        session = self.get(name)
        session.remove_parent()
        session.rmdirs()

    def _add_session_env(self, session_env):
        """Adds the session environment to the session manager"""
        self._add(session_env.name, session_env, push_up=False, check_attr=False)

    @property
    def current_env(self):
        """Current session environment"""
        if self._current_session is None:
            return None
        return self.get(self._current_session)

    @property
    def current(self):
        """Returns the current session"""
        if self._current_session is None:
            return None
        return self.get_session(self._current_session)

    def set_current(self, name):
        """Sets the current session name"""
        if name in self.sessions:
            self._current_session = name
        else:
            logger.warning("'{}' not in sessions ({})".format(name, ', '.join(self.sessions.keys())))

    @property
    def session_envs(self):
        """Return all session environments"""
        return [env for env in self.list_dirs() if isinstance(env, SessionEnvironment)]

    @property
    def sessions(self):
        """Returns all sessions"""
        return {env.session.name: env.session for env in self.session_envs}

    def get_session(self, name):
        """Gets a AqSession by name"""
        session_env = self.get(name)
        return session_env.session

    def delete_session(self, name):
        """Deletes a session, removing the folders and files as well as the abstract
        MagicDir link"""
        session_env = self.get(name)
        session_env.rmdirs()
        session_env.remove_parent()

    def move_repo(self, path):
        """Move all of the folders to a new location"""
        super().mvdirs(path)
        self.save()

    def save(self):
        """Save the metadata"""
        self.metadata.env.dump_json(
            {
                "root": str(self.abspath),
                'current': self._current_session,
                "updated_at": str(datetime.datetime.now()),
                "version": __version__
            },
            indent=4)
        self.save_environments()

    @classmethod
    def load(cls, path_to_metadata=None):
        """Load from the metadata"""

        if path_to_metadata is None:
            path_to_metadata = os.path.join(
                SessionManager.DEFAULT_METADATA_LOC, SessionManager.DEFAULT_METADATA_NAME)

        with open(path_to_metadata, 'r') as f:
            meta = json.load(f)
            if __version__ != meta['version']:
                logger.warning("Version mismatched! Environment data stored using "
                               "ParrotFish version '{}' but currently using '{}'"
                               .format(meta['version'], __version__))
            env = cls.load_environments(meta['root'])
            env.set_current(meta['current'])
            return env

    def save_environments(self):
        """Save all of the session environments"""
        for session_env in self.session_envs:
            session_env.save_to_pkl()

    @classmethod
    def load_environments(cls, dir):
        """Collects the SessionEnvironment pickles and returns a SessionManager with these
        session_environments

        For examples `dir="User/Documents/Fishtank"` would load a SessionManager with
        the name "Fishtank." Environments would be loaded from `User/Documents/FishTank/*/.env_pkl`
        """
        sm = cls(dir, name=os.path.basename(dir))
        env_pkls = glob(os.path.join(dir, "*", SessionEnvironment.ENV_PKL))
        for env_pkl in env_pkls:
            session_env = SessionEnvironment.load_from_pkl(env_pkl)
            sm._add_session_env(session_env)
        return sm


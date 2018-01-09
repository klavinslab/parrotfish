import datetime
import os
from glob import glob

import dill
from magicdir import MagicDir
from parrotfish.__version__ import __version__
from parrotfish.utils import sanitize_filename, sanitize_attribute
from parrotfish.utils.log import CustomLogging
from pydent import AqSession
from pydent.models import OperationType, Library
import base64
logger = CustomLogging.get_logger(__name__)
from copy import deepcopy

from cryptography.fernet import Fernet, InvalidToken

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

    def __init__(self, name, login, password, aquarium_url, encryption_key):
        """

        :param path: The path of this session
        :type path: str
        """
        super().__init__(name, push_up=False, check_attr=False)

        # set the session
        cipher_suite = Fernet(encryption_key)
        self.encrypted_password = cipher_suite.encrypt(str.encode(password))
        self.login = login
        self.aquarium_url = aquarium_url

        # this should never be saved in the pickle
        self.aquarium_session = self.create_session(encryption_key)

        # add the environment pickle
        self.add_file(self.ENV_PKL, attr='env_pkl')

        # add protocols directory
        self.add('protocols')

    def create_session(self, encryption_key):
        cipher_suite = Fernet(encryption_key)
        aqsession = None
        try:
            aqsession = AqSession(self.login,
                                  cipher_suite.decrypt(self.encrypted_password).decode(),
                                  self.aquarium_url,
                                  name=self.name)
        except InvalidToken:
            logger.warning(self.encrypted_password)
            logger.warning("Encryption key mismatch! Cannot create session. Use 'pfish generate-encryption-key' to generate"
                           "a new key. Alternatively, use 'pfish set-encryption-key [YOURKEY]' if you have a pre-generated"
                           "key")
        self.aquarium_session = aqsession
        return aqsession

    @classmethod
    def load_from_pkl(cls, env_pkl, encryption_key):
        env = None
        if os.path.isfile(env_pkl):
            with open(env_pkl, 'rb') as f:
                env = dill.load(f)
        env.create_session(encryption_key)
        return env

    def save_to_pkl(self):
        """Save to pickle"""
        copied = deepcopy(self)

        # remove aquarium_session from the pickle
        copied.aquarium_session = None
        with self.env_pkl.open('wb') as f:
            dill.dump(copied, f)

    def update_encryption_key(self, old_key, new_key):
        old_cipher = Fernet(old_key)
        new_cipher = Fernet(new_key)
        self.encrypted_password = new_cipher.encrypt(old_cipher.decrypt(self.encrypted_password))

    # def reload_from_pkl(self, encryption_key):
    #     """Load attributes from the pickle"""
    #     with self.env_pkl.open('wb') as f:
    #         sess = self.aquarium_session
    #         loaded = dill.load(f)
    #         vars(self).updated(vars(loaded))
    #         self.aquarium_session = sess

    # def reload_from_pkl(self):
    #     """Load attributes from the pickle"""
    #     with self.env_pkl.open('wb') as f:
    #         loaded = dill.load(f)
    #         vars(self).updated(vars(loaded))

    # @classmethod
    # def load_from_pkl(cls, env_pkl):
    #     """Load from pickle"""
    #     if os.path.isfile(env_pkl):
    #         with open(env_pkl, 'rb') as f:
    #             return dill.load(f)

    def add_category_dir(self, category):
        cat_dirname = sanitize_filename(category)
        cat_dir = self.protocols.add(sanitize_attribute(cat_dirname))
        return cat_dir

    def add_protocol_dir(self, category_name, protocol_name):
        cat = self.add_category_dir(category_name)
        protocol_name = sanitize_filename(protocol_name)
        return cat.add(protocol_name)

    @staticmethod
    def _sanitize_name(name):
        return sanitize_filename(name)

    def get_category_dir(self, cat_name):
        cat_name = self._sanitize_name(cat_name)
        if not self.protocols.has(cat_name):
            raise FileNotFoundError("Category \"{}\" not found".format(cat_name))
        return self.protocols.get(cat_name)

    def get_protocol_dir(self, cat_name, protocol_name):
        cat = self.get_category_dir(cat_name)
        protocol_name = self._sanitize_name(protocol_name)
        if not cat.has(protocol_name):
            raise FileNotFoundError("Protocol \"{}/{}\" not found".format(cat_name, protocol_name))
        return cat.get(protocol_name)

    @property
    def categories(self):
        """Return a list of categories (MagicDir)"""
        return self.protocols.list_dirs()

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
        ot_dir = self.add_protocol_dir(category, operation_type_name)
        basename = ot_dir.name

        # add operation type files
        ot_dir.add_file('{}.json'.format(basename), attr='meta')
        ot_dir.add_file('{}.rb'.format(basename), attr='protocol')
        ot_dir.add_file('{}__precondition.rb'.format(basename), attr='precondition')
        ot_dir.add_file('{}__cost_model.rb'.format(basename), attr='cost_model')
        ot_dir.add_file('{}__documentation.rb'.format(basename), attr='documentation')

        return ot_dir

    def get_library_type_dir(self, category, library_name):
        lib_dir = self.add_protocol_dir(category, library_name)
        basename = lib_dir.name

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
            logger.verbose("    saving {}".format(accessor))
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
        ot.connect_to_session(self.aquarium_session)
        return ot

    def read_library_type(self, category, name):
        lib_dir = self.get_library_type_dir(category, name)
        metadata = lib_dir.meta.load_json()
        lib = Library.load(metadata)

        lib.source.content = lib_dir.source.read()
        lib.connect_to_session(self.aquarium_session)
        return lib


class SessionManager(MagicDir):
    """
    SessionManager reads and writes :class:`OperationType` and :class:`Library`.
    The path of the directory (*SessionManagerName*) is saved in
    *meta_dir/environment_data/meta_name.json* in *root*.

    Example session structure::

        meta_dir
        └──environment_data
            └──meta_name.json       (contains information about root directory)

        SessionManagerName          (Master or root directory)
        |──SessionEnvironment1      (Aquarium session)
        |   └──Category1            (Protocol Category)
        |       |──.env_pkl         (contains information about SessionEnvironment1's AqSession)
        |       |──protocols        (protocols folder)
        |       |   |──OperationType1
        |       |   |   |──OperationType1.json
        |       |   |   |──OperationType1.rb
        |       |   |   |──OperationType1__cost_model.rb
        |       |   |   |──OperationType1__documentation.rb
        |       |   |   └──OperationType1__precondition.rb
        |       |   └──LibraryType1
        |       |       |──LibraryType1.rb
        |       |       └──LibraryType1.json
        |       └──OperationType1
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

        # Add metadata (has default)
        # this is where session manager information will be stored
        if meta_dir is None:
            meta_dir = self.DEFAULT_METADATA_LOC
        if meta_name is None:
            meta_name = self.DEFAULT_METADATA_NAME
        self.metadata = MagicDir(meta_dir)
        self.metadata.add_file(meta_name, 'env')

        self._curr_session_name = None

    def register_session(self, login, password, aquarium_url, name):
        """Registers a new session by creating a AqSession, creating
        a SessionEnvironment and adding it to the SessionManager"""
        if name in self.sessions:
            logger.warning("'{}' already exists!".format(name))
            return
        key = str.encode(self.__meta['encryption_key'])
        session_env = SessionEnvironment(name, login, password, aquarium_url, key)
        self._add_session_env(session_env)

    def remove_session(self, name):
        session = self.get(name)
        session.remove_parent()
        session.rmdirs()

    def _add_session_env(self, session_env):
        """Adds the session environment to the session manager"""
        self._add(session_env.name, session_env, push_up=False, check_attr=False)

    @property
    def __meta(self):
        if not self.metadata.env.exists():
            self.save()
        return self.metadata.env.load_json()

    @property
    def current_env(self):
        """Current session environment"""
        if self._curr_session_name is None:
            return None
        return self.get(self._curr_session_name)

    @property
    def current_session(self):
        """Returns the current session"""
        if self._curr_session_name is None:
            return None
        return self.get_session(self._curr_session_name)

    def set_current(self, name):
        """Sets the current session name"""
        if name is None:
            return
        if name in self.sessions:
            self._curr_session_name = name
        else:
            logger.warning("'{}' not in sessions ({})".format(name, ', '.join(self.sessions.keys())))

    @property
    def session_env_list(self):
        """Return all session environments"""
        return [env for env in self.list_dirs() if isinstance(env, SessionEnvironment)]

    @property
    def sessions(self):
        """Returns all sessions"""
        return {env.name: env.aquarium_session for env in self.session_env_list}

    def get_session(self, name):
        """Gets a AqSession by name"""
        session_env = self.get(name)
        return session_env.aquarium_session

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

    def __new_encryption_key(self):
        return Fernet.generate_key()

    def save(self, force_new_key=False, key=None):
        """Save the metadata"""
        encryption_key = None
        if not self.metadata.env.exists() or force_new_key:
            if key is None:
                logger.warning("No encryption key found. Generating new key...")
                encryption_key = self.__new_encryption_key().decode()
            else:
                encryption_key = key
        else:
            encryption_key = self.metadata.env.load_json()['encryption_key']
        self.metadata.env.dump_json(
            {
                "root": str(self.abspath),
                'current': self._curr_session_name,
                "updated_at": str(datetime.datetime.now()),
                "version": __version__,
                "encryption_key": encryption_key
            },
            indent=4)
        self.save_environments()

    def load(self):
        """Load from the metadata"""
        meta = self.__meta
        if __version__ != meta['version']:
            logger.warning("Version mismatched! Environment data stored using "
                           "ParrotFish version '{}' but currently using '{}'"
                           .format(meta['version'], __version__))
        encryption_key = meta['encryption_key']
        env = self.load_environments(encryption_key)
        env.set_current(meta['current'])
        self.save()
        return env

    def save_environments(self):
        """Save all of the session environments"""
        for session_env in self.session_env_list:
            session_env.save_to_pkl()

    def update_encryption_key(self, new_key):
        old_key = self.__meta['encryption_key']
        for session_env in self.session_env_list:
            if session_env:
                session_env.update_encryption_key(old_key, new_key)

    # TODO: consolidate password hashes here
    def load_environments(self, encryption_key):
        """Collects the SessionEnvironment pickles and returns a SessionManager with these
        session_environments

        For examples `dir="User/Documents/Fishtank"` would load a SessionManager with
        the name "Fishtank." Environments would be loaded from `User/Documents/FishTank/*/.env_pkl`
        """
        meta = self.__meta
        self.name = os.path.basename(self.metadata.env.name)

        # set root path
        root_dir = os.path.dirname(meta['root'])
        root_name = os.path.basename(meta['root'])
        self.set_dir(root_dir)
        self.name = root_name

        env_pkls = glob(os.path.join(str(self.abspath), "*", SessionEnvironment.ENV_PKL))
        for env_pkl in env_pkls:
            session_env = SessionEnvironment.load_from_pkl(env_pkl, encryption_key)
            if session_env is not None:
                self._add_session_env(session_env)
        self.set_current(meta['current'])
        return self

    def __str__(self):
        return "SessionManager(\n" \
               "  name={name}\n" \
               "  current_session={current}\n" \
               "  environment_location=\"{metadata}\"\n" \
               "  session_directory=\"{dir}\")".format(
            name=self.name,
            metadata=str(self.metadata.env.abspath),
            current=self.current_session,
            dir=str(self.abspath)
        )

    def __repr__(self):
        return "SessionManager(name={name}, env={env}".format(name=self.name, env=str(self.metadata.env.abspath))

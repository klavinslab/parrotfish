"""
Classes for managing Aquarium sessions and protocols
"""

import datetime
import os
from glob import glob

import dill
from opath import ODir
from pydent import AqSession
from pydent.models import OperationType, Library

from parrotfish.__version__ import __version__
from parrotfish.utils import sanitize_filename, sanitize_attribute
from parrotfish.utils.log import CustomLogging

logger = CustomLogging.get_logger(__name__)
from copy import deepcopy

from cryptography.fernet import Fernet, InvalidToken


class SessionEnvironment(ODir):
    """
    Manages protocols (:class:`OperationType` & :class:`Library`) for a single Aquarium
    session.

    Features:
        * **fetch** protocols from an Aquarium server and write them to
    the local machine.
        * **push** protocols from the local machine to the Aquarium server

    Directory structure details: Each managed session will contain a directory for each
    :class:`OperationType` or :class:`Library` folder it is managing. The directory structure
    for a managed session looks like the following::

        SessionEnvironment1
           |──.session_env.pkl              (pickled information about the AqSession it is managing)
           └──Category1                     (protocol category folder)
               |──OperationType1            (OperationType folder)
               |   |──OperationType1.json   (data related to OperationType)
               |   |──OperationType1.rb                 (protocol code)
               |   |──OperationType1__cost_model.rb     (code model code)
               |   |──OperationType1__documentation.md  (documentation markdown)
               |   └──OperationType1__precondition.rb   (precondition code)
               └──LibraryType1              (Library folder)
                   |──LibraryType1.rb                   (library code)
                   └──LibraryType1.json                 (data related to the Library)

    Encryption details: Each managed session folder (:class:`SessionEnvironment`)
    also stores information about
    the Aquarium session it uses, which includes login and the url.
    This ties the actual server (i.e. the url) to the managed session folder. For security,
    ParrotFish does *not* directly store the :class:`AqSession.` Instead, passwords are encrypted
    using Fernet (https://cryptography.io/en/latest/fernet/). Passwords are stored as an encrypted
    string. This string can be decrypted using the proper key.
    """

    ENV_PKL = '.session_environment.pkl'  # name of the pickled file when saving or loading

    def __init__(self, name, login, password, aquarium_url, encryption_key):
        """
        Constructs a new :class:`SessionEnvironment`.

        :param name: name of the session
        :type name: str
        :param login: aquarium login
        :type login: str
        :param password: aquarium password (not stored)
        :type password: str
        :param aquarium_url: aquarium url
        :type aquarium_url: str
        :param encryption_key: Fernet encryption key to use to store the encrypted password
        :type encryption_key: str
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
        """Creates a new :class:`AqSession` instance using the login, aquarium_url, and encrypted
        password information stored. The encryption_key is used to decrypt a the password.

        :param encryption_key: Fernet key to decrypt the password
        :type encryption_key: str
        :return: AqSession instance
        :rtype: AqSession
        """
        cipher_suite = Fernet(encryption_key)
        aqsession = None
        try:
            aqsession = AqSession(self.login,
                                  cipher_suite.decrypt(self.encrypted_password).decode(),
                                  self.aquarium_url,
                                  name=self.name)
        except InvalidToken:
            logger.warning(self.encrypted_password)
            logger.warning(
                "Encryption key mismatch! Cannot create session. Use 'pfish generate-encryption-key' to generate"
                " a new key. Alternatively, use 'pfish set-encryption-key [YOURKEY]' if you have a pre-generated"
                " key")
        self.aquarium_session = aqsession
        return aqsession

    @classmethod
    def load_from_pkl(cls, env_pkl, encryption_key):
        """Loads from the pickle"""
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
        """
        Updates the encryption key for this SessionEnvironment

        :param old_key: old Fernet key
        :type old_key: str
        :param new_key: new Fernet key
        :type new_key: str
        :return: None
        :rtype: None
        """
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
        """Creates a new category directory"""
        cat_dirname = sanitize_filename(category)
        cat_dir = self.protocols.add(sanitize_attribute(cat_dirname))
        return cat_dir

    def add_protocol_dir(self, category_name, protocol_name):
        """Creates a new protocol directory"""
        cat = self.add_category_dir(category_name)
        protocol_name = sanitize_filename(protocol_name)
        return cat.add(protocol_name)

    @staticmethod
    def _sanitize_name(name):
        """Sanitizes a name to make it *file friendly*"""
        return sanitize_filename(name)

    def get_category_dir(self, cat_name):
        """
        Returns the :class:`ODir` that manages a category

        :param cat_name: category name
        :type cat_name: str
        :return: category directory
        :rtype: ODir
        """
        cat_name = self._sanitize_name(cat_name)
        if not self.protocols.has(cat_name):
            raise FileNotFoundError("Category \"{}\" not found".format(cat_name))
        return self.protocols.get(cat_name)

    def get_protocol_dir(self, cat_name, protocol_name):
        """
        Returns the :class:`ODir` that manages the protocol

        :param cat_name: category of the protocol
        :type cat_name: str
        :param protocol_name: name of the protocol
        :type protocol_name: str
        :return: directory that manages the protocol
        :rtype: ODir
        """
        cat = self.get_category_dir(cat_name)
        protocol_name = self._sanitize_name(protocol_name)
        if not cat.has(protocol_name):
            raise FileNotFoundError("Protocol \"{}/{}\" not found".format(cat_name, protocol_name))
        return cat.get(protocol_name)

    @property
    def categories(self):
        """Return a list of categories (ODir)"""
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
        """
        Returns the :class:`ODir` that manages an operation_type

        :param category: category of the OperationType
        :type category: str
        :param operation_type_name: name of the operation_type
        :type operation_type_name: str
        :return: the library directory
        :rtype: ODir
        """
        ot_dir = self.add_protocol_dir(category, operation_type_name)
        basename = ot_dir.name

        # add operation type files
        ot_dir.add_file('{}.json'.format(basename), attr='meta')
        ot_dir.add_file('{}.rb'.format(basename), attr='protocol')
        ot_dir.add_file('{}__precondition.rb'.format(basename), attr='precondition')
        ot_dir.add_file('{}__cost_model.rb'.format(basename), attr='cost_model')
        ot_dir.add_file('{}__documentation.md'.format(basename), attr='documentation')

        return ot_dir

    def get_library_type_dir(self, category, library_name):
        """
        Returns the :class:`ODir` library that manages a library

        :param category: category of the Library
        :type category: str
        :param library_name: name of the library
        :type library_name: str
        :return: the library directory
        :rtype: ODir
        """
        lib_dir = self.add_protocol_dir(category, library_name)
        basename = lib_dir.name

        # add library source file
        lib_dir.add_file('{}.json'.format(basename), attr='meta')
        lib_dir.add_file('{}.rb'.format(basename), attr='source')

        return lib_dir

    def write_operation_type(self, operation_type):
        """
        Writes a :class:`OperationType` to the local machine

        :param operation_type: OperationType to write to local files
        :type operation_type: OperationType
        :return: None
        :rtype: None
        """
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
        """
        Writes a :class:`Library` to the local machine

        :param library: library to write to local files
        :type library: Library
        :return: None
        :rtype: None
        """
        lib_dir = self.get_library_type_dir(library.category, library.name)

        # write json
        lib_dir.meta.dump_json(library.dump(include={'source'}), indent=4)

        # write codes
        lib_dir.source.write(library.code('source').content)

    def read_operation_type(self, category, name):
        """
        Constructs a :class:`OperationType` instance constructed out of local
        files

        :param category: category of the protocol
        :type category: str
        :param name: name of the protocol
        :type name: str
        :return: OperationType read from local files
        :rtype: OperationType
        """
        ot_dir = self.get_operation_type_dir(category, name)
        metadata = ot_dir.meta.load_json()  # load the meta data from the .json file
        ot = OperationType.load_from(metadata, self.aquarium_session)

        for accessor in ['protocol', 'precondition', 'cost_model', 'documentation']:
            code = getattr(ot, accessor)
            code.content = ot_dir.get(accessor).read()
        return ot

    def read_library_type(self, category, name):
        """
        Constructs a :class:`Library` instance constructed out of local
        files

        :param category: category of the protocol
        :type category: str
        :param name: name of the protocol
        :type name: str
        :return: library read from local files
        :rtype: Library
        """
        lib_dir = self.get_library_type_dir(category, name)
        metadata = lib_dir.meta.load_json()
        lib = Library.load_from(metadata, self.aquarium_session)

        source = lib.source
        source.content = lib_dir.source.read()
        return lib

    # def get_optype_test(self, operation_type):
    #     self.add

    def _test_category_name(self, category_name):
        cat_dirname = 'test_' + sanitize_filename(category_name)
        return cat_dirname.lower()

    def _boilerplate_path(self):
        here = os.path.abspath(os.path.dirname(__file__))
        boilerplate_path = os.path.join(here, 'data', 'boilerplate', 'pytest')
        return boilerplate_path

    def _create_pytest_boilerplate(self, session):
        boilerplate_path = self._boilerplate_path()

        # create outer tests/conftest.py
        with open(os.path.join(boilerplate_path, 'conftest.py.txt'), 'r') as f:
            self.add('tests').write_file('conftest.py', mode='w', data=f.read())

        session_dir = self.get('tests').add(session.name)
        with open(os.path.join(boilerplate_path, 'conftest.py.session.txt'), 'r') as f:
            txt = f.read().format(session_name=session.name)
            session_dir.write_file('conftest.py', mode='w', data=txt)

        with open(os.path.join(self._boilerplate_path(), 'test.py.txt'), 'r') as f:
            bp_test_code = f.read()

        for cat in self.categories:
            category = cat.name
            cat_test_dir = session_dir.add(self._test_category_name(category))
            with open(os.path.join(boilerplate_path, 'conftest.py.category.txt'), 'r') as f:
                txt = f.read().format(category_name=cat.name)
                cat_test_dir.write_file('conftest.py', mode='w', data=txt)

            for ot_dir in cat.list_dirs():
                # ot_dir = self.get_operation_type_dir(category, name)
                metadata = ot_dir.meta.load_json()  # load the meta data from the .json file
                ot = OperationType.load_from(metadata, self.aquarium_session)
                filename = 'test_{}.py'.format(sanitize_filename(ot.name))
                txt = bp_test_code.format(optype_name=ot.name)
                cat_test_dir.write_file(filename, mode='w', data=txt)


class SessionManager(ODir):
    """
    Manages multiple :class:`SessionEnvironment` instances. SessionEnvironments live
    in a single directory managed by this class. Information about where the SessionManager
    directory resides is stored in the 'environment_data/environment_settings.json` file.
    By default, this is located where ParrotFish is installed so that is can be used globally
    on the machine. Alternatively, a SessionManager can be constructed that uses a new
    environement_settings file. The **environment_settings.json** also stores an
    important encryption key so that :class:`SessionEnvironment`s can be decrypted and used properly.

    Example session structure::

        meta_dir
        └──environment_data
            └──environment_settings.json       (contains information about root directory)

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

    DEFAULT_METADATA_LOC = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'environment_data')
    DEFAULT_METADATA_NAME = 'environment_settings.json'

    def __init__(self, dir, name="FishTank", config_dir=None, config_name=None):
        """
        SessionManager constructor

        :param dir: directory
        :type dir: str
        :param name: name of the folder
        :type name: str
        :param config_dir: directory to store the metadata
        :type config_dir: str
        :param config_name: name of the file to store the metadata
        :type config_name: str
        """
        super().__init__(name, push_up=False, check_attr=False)
        self.set_dir(dir)

        # Add metadata (has default)
        # this is where session manager information will be stored
        if config_dir is None:
            config_dir = self.DEFAULT_METADATA_LOC
        if config_name is None:
            config_name = self.DEFAULT_METADATA_NAME
        self.config = ODir(config_dir)
        self.config.add_file(config_name, 'env_settings')

        self._curr_session_name = None

    def register_session(self, login, password, aquarium_url, name):
        """Registers a new session by creating a AqSession, creating
        a SessionEnvironment and adding it to the SessionManager"""
        if name in self.sessions:
            logger.warning("'{}' already exists!".format(name))
            return
        key = str.encode(self.__config['encryption_key'])
        session_env = SessionEnvironment(name, login, password, aquarium_url, key)
        self._add_session_env(session_env)

    def remove_session(self, name):
        """
        Removes and deletes a managed session

        :param name: name of the session to delete
        :type name: str
        :return: None
        :rtype: None
        """
        session = self.get(name)
        session.remove_parent()
        session.rmdirs()

    def _add_session_env(self, session_env):
        """Adds the session environment to the session manager"""
        self._add(session_env.name, session_env, push_up=False, check_attr=False)

    @property
    def __config(self):
        if not self.config.env_settings.exists():
            self.save()
        return self.config.env_settings.load_json()

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
        ODir link"""
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
        if not self.config.env_settings.exists() or force_new_key:
            if key is None:
                logger.warning("No encryption key found. Generating new key...")
                encryption_key = self.__new_encryption_key().decode()
            else:
                encryption_key = key
        else:
            encryption_key = self.config.env_settings.load_json()['encryption_key']
        self.config.env_settings.dump_json(
            {
                "root": str(self.abspath),
                'current': self._curr_session_name,
                "updated_at": str(datetime.datetime.now()),
                "version": __version__,
                "encryption_key": encryption_key
            },
            indent=4)
        self.save_environments()

    def load(self, meta=None):
        """Load from the metadata"""
        if meta is None:
            meta = self.__config
        if __version__ != meta['version']:
            logger.warning("Version mismatched! Environment data stored using "
                           "ParrotFish version '{}' but currently using '{}'"
                           .format(meta['version'], __version__))

        # load encryption key from meta
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
        """Updates the encryption key used to decrypt :class:`SessionEnvironment`s"""
        old_key = self.__config['encryption_key']
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
        meta = self.__config
        self.name = os.path.basename(self.config.env_settings.name)

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
            metadata=str(self.config.env_settings.abspath),
            current=self.current_session,
            dir=str(self.abspath)
        )

    def __repr__(self):
        return "SessionManager(name={name}, env={env}".format(name=self.name, env=str(self.config.env_settings.abspath))

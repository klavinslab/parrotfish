"""
Core functions for interacting with ParrotFish
"""

import os
import tempfile
from pathlib import Path

import fire
from cryptography.fernet import Fernet
from requests.exceptions import InvalidSchema

from parrotfish.session_environment import SessionManager
from parrotfish.utils import CustomLogging, format_json, compare_content

logger = CustomLogging.get_logger(__name__)
logger.setLevel("VERBOSE")
from parrotfish.shell import Shell
from parrotfish.utils import testing_tools
import json


class CLI(object):
    def __init__(self, sm):
        """
        CLI instantiator

        :param sm: SessionManager instance to create a CLI from
        :type sm: SessionManager
        """
        self._session_manager = sm

    def _check_for_session(self):
        """Verifies that there is a current session set"""
        if self._session_manager.current_session is None:
            raise Exception(
                "You must be logged in. Register an Aquarium session.")

    def _save(self):
        """Saves the environment"""
        self._session_manager.save()

    def session(self):
        """Returns the current session"""
        return self._session_manager.current_session

    def _sessions_json(self):
        """Returns a dictionary of sessions"""
        sess_dict = {}
        for session_name, session in self._session_manager.sessions.items():
            val = str(session)
            sess_dict[session_name] = val
        return sess_dict

    def _get_categories(self):
        """Returns dictionary of category names and Library/OperationType"""
        categories = {}
        operation_types = self._session_manager.current_session.OperationType.all()
        libraries = self._session_manager.current_session.Library.all()
        for ot in operation_types:
            l = categories.get(ot.category, [])
            l.append(ot)
            categories[ot.category] = l
        for lib in libraries:
            l = categories.get(lib.category, [])
            l.append(lib)
            categories[lib.category] = l
        return categories

    def _load(self, path_to_metadata=None):
        """Loads the environment"""
        try:
            self._session_manager.load()
            logger.cli("Environment file loaded from \"{}\"".format(self._session_manager.config.env_settings.abspath))
            logger.cli("environment loaded")
            self._save()
            self.print_env()
            return self._session_manager
        except Exception:
            raise Exception("There was an error loading session_manager")

    def print_env(self):
        logger.cli(str(self._session_manager))

    def push_all(self):
        """Save protocol"""
        self._check_for_session()
        current_env = self._session_manager.current_env
        categories = current_env.categories
        for cat in categories:
            self.push_category(cat)

    def push_category(self, category_name):
        """Push all :class:`OperationType` and :class:`Library` in a category"""
        current_env = self._session_manager.current_env
        category = current_env.get_category_dir(category_name)
        for protocol in category.list_dirs():
            local_protocol = None
            accessors = []
            if protocol.has("source"):
                local_protocol = current_env.read_library_type(category.name, protocol.name)
                accessors = ["source"]
            elif protocol.has("protocol"):
                local_protocol = current_env.read_operation_type(category.name, protocol.name)
                accessors = ['protocol', 'precondition', 'documentation', 'cost_model']
            for accessor in accessors:
                code = getattr(local_protocol, accessor)
                server_code = local_protocol.code(accessor)
                diff_str = compare_content(server_code.content, code.content).strip()
                if diff_str != '':
                    logger.cli("++ Updating {}/{} ({})".format(category.name, local_protocol.name, accessor))
                    print(diff_str)
                    code.update()
                else:
                    logger.cli("-- No changes for {}/{} ({})".format(category.name, local_protocol.name, accessor))
        self._save()

    def _get_operation_types_from_sever(self, category, name=None):
        query = {"category": category}
        if name:
            query['name'] = name
        return self._session_manager.current_session.OperationType.where(query)

    def _get_library_types_from_server(self, category, name=None):
        query = {"category": category}
        if name:
            query['name'] = name
        return self._session_manager.current_session.Library.where(query)

    def _get_all_operation_types_from_server(self):
        return self._session_manager.current_session.OperationType.all()

    def _get_all_library_types_from_server(self):
        return self._session_manager.current_session.Library.all()

    def fetch_all(self):
        """Fetches all protocols from the current session"""
        self._check_for_session()
        ots = self._get_all_operation_types_from_server()
        libs = self._get_all_library_types_from_server()
        self._fetch(ots, libs)

    def _fetch(self, ots, libs):
        logger.cli("{} operation_types found".format(len(ots)))
        logger.cli("This may take awhile...")
        total = len(ots) + len(libs)
        counter = 0

        make_msg = lambda m, count: "{}/{} saving {}:{}".format(count, total, m.category, m.name)

        for ot in ots:
            counter += 1
            msg = make_msg(ot, counter)
            try:
                logger.cli(msg)
                curr_env = self._session_manager.current_env
                curr_env.write_operation_type(ot)
            except TypeError as e:
                logger.error("Could not fetch {}.\n{}".format(ot.name, e))
        for lib in libs:
            counter += 1
            msg = make_msg(lib, counter)
            try:
                logger.cli(msg)
                curr_env = self._session_manager.current_env
                curr_env.write_library(lib)
            except TypeError as e:
                logger.error("Could not fetch {}\n{}.".format(lib.name, e))
        self._save()

    def fetch(self, category, name=None):
        """ Fetch protocols from the current session & category and pull to local repo. """
        self._check_for_session()
        ots = self._get_operation_types_from_sever(category, name=name)
        libs = self._get_library_types_from_server(category, name=name)
        self._fetch(ots, libs)

    @property
    def _sessions(self):
        return self._session_manager.sessions

    @property
    def sessions(self):
        """List the current available sessions"""
        sessions = self._sessions
        if len(sessions) == 0:
            logger.cli(
                "There are no sessions. Use 'pfish register' to register a session. Use 'pfish register --h' for help.")
        else:
            logger.cli(format_json(self._sessions_json()))
        return sessions

    def protocols(self):
        """Print category and protocol names"""
        env = self._session_manager.current_env
        cats = env.categories
        for cat in cats:
            for code in cat.dirs:
                logger.cli(cat.name + "/" + code.name)

    def categories(self):
        """ Get all available categories and count """
        self._check_for_session()
        logger.cli("Getting category counts:")
        categories = self._get_categories()
        category_count = {k: len(v) for k, v in categories.items()}
        logger.cli(format_json(category_count))

    def set_session(self, session_name):
        """ Set the session by name. Use "sessions" to find all available sessions. """
        sessions = self._session_manager.sessions
        if session_name not in sessions:
            logger.error("Session \"{}\" not in available sessions ({})".format(session_name, ', '
                                                                                              ''.join(sessions.keys())))

        logger.cli("Setting session to \"{}\"".format(session_name))
        self._session_manager.set_current(session_name)
        self._save()

    def set_repo(self, path):
        repo_dir = os.path.dirname(path)
        repo_name = os.path.basename(path)
        logger.cli("Setting repo to \"{}\"".format(path))
        self._session_manager = SessionManager(repo_dir, name=repo_name)

        logger.cli("Loading environment...")
        self._save()
        self._load()
        logger.cli("{} session(s) loaded".format(len(self._sessions)))

    def move_repo(self, path):
        """Moves the current repo to another location."""
        path = Path(path).absolute()
        if not path.is_dir():
            raise Exception("Path {} does not exist".format(str(path)))
        logger.cli("Moving repo location from {} to {}".format(
            self._session_manager.abspath, path))
        self._session_manager.move_repo(path)
        self._save()

    def reset(self):
        self._session_manager.config.rmdirs()
        self._session_manager.rmdirs()
        self._session_manager.save(force_new_key=True)

    def generate_encryption_key(self):
        key = Fernet.generate_key().decode()
        logger.warning("SAVE THIS KEY IN A SECURE PLACE IF YOU WANT TO USE YOUR REPO ON ANOTHER COMPUTER. "
                       "IT WILL NOT APPEAR AGAIN.")
        logger.warning("NEW KEY: {}".format(key))
        self.__update_encryption_key(key)

    def __update_encryption_key(self, new_key):
        logger.cli("UPDATING KEYS AND PASSWORD HASHES")
        self._session_manager.update_encryption_key(new_key)
        self.set_encryption_key(new_key)

    def set_encryption_key(self, key):
        """
        Sets the encryption key to use for the managed folder.

        :param key:
        :type key:
        :return:
        :rtype:
        """
        logger.cli("Encryption key set")
        self._session_manager.save(force_new_key=True, key=key)
        self._session_manager = SessionManager('').load()
        self._save()
        logger.cli("Loaded sessions with new key")
        return self.sessions

    def register(self, login, password, aquarium_url, name):
        """
        Registers a new session, creating a new managed folder.

        :param login: aquarium login
        :type login: str
        :param password: aquarium password
        :type password: str
        :param aquarium_url: aquarium url
        :type aquarium_url: str
        :param name: name to give to the new session
        :type name: str
        :return: None
        :rtype: NOne
        """
        try:
            self._session_manager.register_session(login, password,
                                                   aquarium_url, name)
        except InvalidSchema:
            raise InvalidSchema("Missing schema for {}. Did you forget the \"http://\"?"
                                .format(aquarium_url))
        logger.cli("registering session: {}".format(name))
        self.set_session(name)
        self._save()

    def unregister(self, name):
        """
        Unregisters a session by name

        :param name: name of session to unregister
        :type name: str
        :return: None
        :rtype: NOne
        """
        if name in self._session_manager.sessions:
            logger.cli("Unregistering {}: {}".format(
                name, str(self._session_manager.get_session(name))))
            self._session_manager.remove_session(name)
        else:
            logger.cli("Session {} does not exist".format(name))
        self._save()

    def ls(self):
        """List dictionary structure for the session manager"""
        logger.cli(str(self._session_manager.abspath))
        logger.cli('\n' + self._session_manager.show())

    def repo(self):
        """Prints the location of the managed folder"""
        logger.cli(str(self._session_manager.abspath))

    def shell(self):
        """Opens an interactive shell"""
        logger.cli("Opening new shell")
        Shell(self).run()

    def _run_test_on_operation_type(self, ot, batch_num, use_precondition):
        """

        :param ot: OperationType
        :type ot: pydent.models.OperationType
        :return: None
        :rtype: None
        """
        result = testing_tools.run_operation_test_with_random(ot, 5, use_precondition=use_precondition)
        return result

    def run_test(self, category, operation_type_name, batch_num, use_precondition=True):
        """
        Run test on a particular operation

        :param category:
        :type category:
        :param operation_type_name:
        :type operation_type_name:
        :return: None
        :rtype: None
        """
        ots = self.session().OperationType.where({"category": category, "name": operation_type_name})
        if len(ots) == 0:
            logger.error("No operation types found")
            return None
        if not len(ots) == 1:
            logger.warn("{} operation types found for {}:{}".format(len(ots), category, operation_type_name))
        results = []
        for ot in ots:
            result = self._run_test_on_operation_type(ot, batch_num, use_precondition)
            results.append(result)
        self._print_test_results(results)
        return results

    def run_tests(self, category, batch_num, use_precondition=True):
        """
        Run tests on a category

        :param category: category name
        :type category: basestring
        :return: None
        :rtype: None
        """
        ots = self.session().OperationType.where({"category": category})
        results = {}
        for ot in ots:
            result = self._run_test_on_operation_type(ot, batch_num, use_precondition=use_precondition)
            results[ot.name] = result
        self._print_test_results(results)
        return results

    def _print_test_results(self, results):
        for result in results:
            ot = result['operations'][0].operation_type
            print("{} (id={}, deployed={})".format(ot.name, ot.id, ot.deployed))
            print("Passed: {}".format(result['passed']))
            print(json.dumps(result['operation_statuses'], indent=4))

    def __str__(self):
        return str(self._session_manager)

    def create_pytest_boilerplate(self):
        """Creates pytest boilerplate code in the current sessions directory."""
        env = self._session_manager.current_env
        env._create_pytest_boilerplate(self._session_manager.current_session)


def open_from_global():
    """
    Opens a CLI instance from globally stored environment file that points
    to a particular directory on the local machine.

    :return: CLI instance
    :rtype: CLI
    """
    sm = SessionManager(tempfile.mkdtemp())
    sm.load()
    cli = CLI(sm)
    return cli


def open_from_local(directory, encryption_key=None):
    """
    Opens a CLI instance from within a parrotfish directory. For example,
    if the following exists::

        FishTank          (Master or root directory)
        |──nursery      (Aquarium session)
        |   └──Category1            (Protocol Category)
        |       |──.env_pkl         (contains information about SessionEnvironment1's AqSession)
        |       |──protocols        (protocols folder)

    this method will attempt to open "FishTank" using the 'env.json' located within
    FishTank. If it does not exist and an encryption key is provided, a new 'env.json'
    will be created.

    :param directory: directory path pointing to the parrotfish folder
    :type directory: str
    :param encryption_key: optional encryption_key to use
    :type encryption_key: str
    :return: CLI instance
    :rtype: CLI
    """
    sm_dir = os.path.dirname(directory)
    sm_name = os.path.basename(directory)
    sm = SessionManager(sm_dir, sm_name, config_dir=directory)
    if encryption_key:
        sm.update_encryption_key(encryption_key)
    sm.load()
    cli = CLI(sm)
    cli._save()
    return cli


def run():
    logger.setLevel("VERBOSE")
    cli = open_from_global()
    fire.Fire(cli)


if __name__ == '__main__':
    run()

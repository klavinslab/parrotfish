"""
Core functions for interacting with ParrotFish
"""

import os
import tempfile
from pathlib import Path

from opath.utils import rmtree, copytree

import fire
from cryptography.fernet import Fernet
from colorama import Fore
from parrotfish.session_environment import SessionManager
from parrotfish.utils import (CustomLogging, docker_testing,
                              format_json, compare_content)
from parrotfish.shell import Shell
from requests.exceptions import InvalidSchema

logger = CustomLogging.get_logger(__name__)
logger.setLevel("VERBOSE")


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
        operation_types = self.session.OperationType.all()
        libraries = self._session_manager.current_session.Library.all()
        for ot in operation_types:
            category_list = categories.get(ot.category, [])
            category_list.append(ot)
            categories[ot.category] = category_list
        for lib in libraries:
            category_list = categories.get(lib.category, [])
            category_list.append(lib)
            categories[lib.category] = category_list
        return categories

    def _load(self, path_to_metadata=None):
        """Loads the environment"""
        try:
            self._session_manager.load()
            logger.cli("Environment file loaded from \"{}\"".format(
                self._session_manager.metadata.env_settings.abspath))
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
        """
        Push all :class:`OperationType` and :class:`Library` in a category.
        """
        current_env = self._session_manager.current_env
        category = current_env.get_category_dir(category_name)
        for protocol in category.list_dirs():
            self.push_one(category.name, protocol.name)

    def push_one(self, category_name, protocol_name, force=False):
        current_env = self._session_manager.current_env
        category = current_env.get_category_dir(category_name)
        protocol = current_env.get_protocol_dir(category_name, protocol_name)
        if protocol.has("source"):
            # then its a Library
            local_lib = current_env.read_library_type(
                category.name, protocol.name)
            local_lib.code("source").update()
        if protocol.has("protocol"):
            # then its an OperationType
            local_ot = current_env.read_operation_type(
                category.name, protocol.name)
            # TODO: unify accessing this list - used elsewhere
            for accessor in ['protocol', 'precondition',
                             'documentation', 'cost_model']:
                code = getattr(local_ot, accessor)
                server_code = local_ot.code(accessor)

                diff_str = compare_content(
                    server_code.content, code.content).strip()
                if diff_str != '':
                    # Local change, so fetch remote and compare
                    remote_ot = self.session.OperationType.where(
                        {"category": category.name, "name": protocol.name})[0]
                    remote_code = getattr(remote_ot, accessor)
                    if code.id != remote_code.id and force is False:
                        msg = "Local version of {}/{} ({}) out of date. "
                        "Please fetch before pushing again"
                        logger.cli(Fore.RED + msg.format(
                            category.name, protocol.name, accessor))
                    else:
                        logger.cli(
                            "++ Updating {}/{} ({})".format(category.name,
                                                            local_ot.name,
                                                            accessor))
                        print(diff_str)
                        code.update()
                else:
                    logger.cli(
                        "-- No changes for {}/{} ({})".format(category.name,
                                                              local_ot.name,
                                                              accessor))
            self._save()

    def _get_operation_types_from_sever(self, category):
        return self._session_manager.current_session.OperationType.where(
            {"category": category})

    def _get_library_types_from_server(self, category):
        return self._session_manager.current_session.Library.where(
            {"category": category})

    def fetch(self, category):
        """
        Fetch protocols from the current session and category and pull to local
        repo.
        """
        self._check_for_session()
        ots = self._get_operation_types_from_sever(category)
        libs = self._get_library_types_from_server(category)
        logger.cli("{} operation_types found".format(len(ots)))
        logger.cli("This may take awhile...")
        for ot in ots:
            logger.cli("Saving {}".format(ot.name))
            curr_env = self._session_manager.current_env
            curr_env.write_operation_type(ot)
        for lib in libs:
            logger.cli("Saving {}".format(lib.name))
            curr_env = self._session_manager.current_env
            curr_env.write_library(lib)
        self._save()

    def test(self, category_name, protocol_name, reset=False):
        """ Test a single protocol on an Aquarium Docker container """
        session = self._session_manager.current_session
        session_name = session.name

        try:
            # Start container
            self.start_container(reset)

            # Init container session
            logger.cli("Setting Docker session")
            self.register(
                "neptune",
                "aquarium",
                "http://localhost:3001",
                "docker")
            self.set_session("docker")

            # Copy OT from last session to container session
            logger.cli(
                "Copying protocol from {} to docker session".format(
                    session_name))
            ot = session.OperationType.find_by_name(protocol_name)
            self._copy_operation_type(session_name, "docker", ot)

            # Load data to container
            logger.cli("Loading test data into container")
            current_env = self._session_manager.current_env
            protocol = current_env.get_protocol_dir(
                category_name, protocol_name)
            testing_data = docker_testing.load_data(protocol)

            # Push OT from container session to container
            logger.cli("Pushing protocol: {}".format(protocol_name))
            current_env.write_operation_type(testing_data['ot'], no_code=True)
            self.push_one(category_name, protocol_name, force=True)

            # Test protocol on container
            logger.cli("Testing protocol: {}".format(protocol_name))
            result = docker_testing.test_protocol(protocol, testing_data)

            # Remove container session
            logger.cli("Unregistering Docker session")
            self.unregister("docker")
            self.set_session(session_name)

            logger.cli("Plan success: {}".format(result['success']))
            logger.cli("View plan: {}".format(result['plan_url']))
        except Exception:
            self.unregister("docker")
            self.set_session(session_name)
            raise

    def start_container(self, reset=False):
        """Start an Aqarium Docker container"""
        container_id = self._session_manager.get_container_id()
        result = docker_testing.start_container(reset, container_id)

        if result['success']:
            logger.cli("Container started!")
        else:
            logger.cli("Container already running: use --reset to restart")
        self._session_manager.set_container_id(result['id'])

    def stop_container(self):
        """Stop an Aqarium Docker container"""
        container_id = self._session_manager.get_container_id()
        if container_id != '':
            docker_testing.stop_container(container_id)
            self._session_manager.set_container_id('')
            logger.cli("Container killed")
        else:
            logger.cli("No container is currently running")

    def _copy_operation_type(self, sess1_name, sess2_name, ot):
        """Copy Operation Type files from one session to another"""
        sess1 = self._session_manager.get(sess1_name)
        sess2 = self._session_manager.get(sess2_name)

        # Copy all files from current_session to docker
        rmtree(sess2.abspath)
        copytree(sess1.abspath, sess2.abspath)

        # Make this operation type visible to ODir
        sess2.get_operation_type_dir(ot.category, ot.name)

    @property
    def _sessions(self):
        return self._session_manager.sessions

    @property
    def sessions(self):
        """List the current available sessions"""
        sessions = self._sessions
        if len(sessions) == 0:
            logger.cli(
                "There are no sessions. "
                "Use 'pfish register' to register a session. "
                "Use 'pfish register --h' for help.")
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
        """
        Set the session by name.
        Use "sessions" to find all available sessions.
        """
        sessions = self._session_manager.sessions
        if session_name not in sessions:
            msg = "Session \"{}\" not in available sessions ({})"
            logger.error(msg.format(session_name, ', '.join(sessions.keys())))

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
        self._session_manager.metadata.rmdirs()
        self._session_manager.rmdirs()
        self._session_manager.save(force_new_key=True)

    def generate_encryption_key(self):
        key = Fernet.generate_key().decode()
        logger.warning(
            "SAVE KEY IN A SECURE PLACE TO USE YOUR REPO ON ANOTHER COMPUTER. "
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
            raise InvalidSchema(
                "Missing schema for {}. Did you forget the \"http://\"?"
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

    def __str__(self):
        return str(self._session_manager)


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
        |       |──.env_pkl         (SessionEnvironment1's AqSession)
        |       |──protocols        (protocols folder)

    this method will attempt to open "FishTank" using the 'env.json' located
    within FishTank.
    If it does not exist and an encryption key is provided, a new 'env.json'
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
    sm = SessionManager(sm_dir, sm_name, meta_dir=directory)
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

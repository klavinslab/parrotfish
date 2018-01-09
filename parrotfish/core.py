from pathlib import Path

import fire

from parrotfish.session_environment import SessionManager
from parrotfish.utils import CustomLogging, format_json, compare_content
from requests.exceptions import InvalidSchema
import tempfile
import os
from cryptography.fernet import Fernet

logger = CustomLogging.get_logger(__name__)
from parrotfish.shell import Shell

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
            logger.cli("Environment file loaded from \"{}\"".format(self._session_manager.metadata.env.abspath))
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
            if protocol.has("source"):
                # then its a Library
                local_lib = current_env.read_library_type(category.name, protocol.name)
                local_lib.code("source").update()
            if protocol.has("protocol"):
                # then its an OperationType
                local_ot = current_env.read_operation_type(category.name, protocol.name)
                for accessor in ['protocol', 'precondition', 'documentation', 'cost_model']:
                    code = getattr(local_ot, accessor)
                    server_code = local_ot.code(accessor)
                    diff_str = compare_content(server_code.content, code.content).strip()
                    if diff_str != '':
                        logger.cli("++ Updating {}/{} ({})".format(category.name, local_ot.name, accessor))
                        print(diff_str)
                        code.update()
                    else:
                        logger.cli("-- No changes for {}/{} ({})".format(category.name, local_ot.name, accessor))
        self._save()

    def _get_operation_types_from_sever(self, category):
        return self._session_manager.current_session.OperationType.where({"category": category})

    def _get_library_types_from_server(self, category):
        return self._session_manager.current_session.Library.where({"category": category})

    def fetch(self, category):
        """ Fetch protocols from the current session & category and pull to local repo. """
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

    @property
    def _sessions(self):
        return self._session_manager.sessions

    @property
    def sessions(self):
        """List the current available sessions"""
        sessions = self._sessions
        if len(sessions) == 0:
            logger.cli("There are no sessions. Use 'pfish register' to register a session. Use 'pfish register --h' for help.")
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

    # def set(session_name, category):
    #     """Sets the session and category"""
    #     set_session(session_name)
    #     set_category(category)


    def set_repo(self, path):
        dir = os.path.dirname(path)
        name = os.path.basename(path)
        logger.cli("Setting repo to \"{}\"".format(path))
        self._session_manager = SessionManager(dir, name=name)

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
        logger.cli("SAVE THIS KEY IN A SECURE PLACE IF YOU WANT TO USE YOUR REPO ON ANOTHER COMPUTER. "
                   "IT WILL NOT APPEAR AGAIN.")
        logger.cli("NEW KEY: {}".format(key))
        self.__update_encryption_key(key)

    def __update_encryption_key(self, new_key):
        logger.cli("UPDATING KEYS AND PASSWORD HASHES")
        self._session_manager.update_encryption_key(new_key)
        self.set_encryption_key(new_key)

    def set_encryption_key(self, key):
        logger.cli("Encryption key set")
        self._session_manager.save(force_new_key=True, key=key)
        self._session_manager = SessionManager('').load()
        self._save()
        logger.cli("Loaded sessions with new key")
        self.sessions

    def register(self,
                 login,
                 password,
                 aquarium_url,
                 name):
        """Registers a new session."""
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
        logger.cli(str(self._session_manager.abspath))

    def shell(self):
        logger.cli("Opening new shell")
        Shell(self).run()


    def __str__(self):
        return str(self._session_manager)


def run():
    logger.setLevel("VERBOSE")
    sm = SessionManager(tempfile.mkdtemp())
    sm.load()
    cli = CLI(sm)
    fire.Fire(cli)


if __name__ == '__main__':
    run()

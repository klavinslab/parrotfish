import os
from pathlib import Path

import fire

from parrotfish.session_environment import SessionManager
from parrotfish.utils import CustomLogging, logging, format_json
from pydent.models import OperationType, Library
from requests.exceptions import InvalidSchema

logger = CustomLogging.get_logger(__name__)


class ParrotFish(object):
    """Contains command and methods for updating and pushing protocols from Aquarium. Automatically
    exposes commands to the command line interface (CLI) using Fire.
    """

    controllers = [
        (OperationType, "protocol"),
        (Library, "source")
    ]

    def __init__(self, session_manager=None):
        """
        ParrotFish constructor

        :param session_manager: The session manager to use
        :type session_manager: SessionManager
        """
        self.session_manager = session_manager

    def check_for_session(self):
        if self.session_manager.current is None:
            raise Exception(
                "You must be logged in. Register an Aquarium session.")

    def save(self):
        """Saves the environment"""
        self.session_manager.save()

    def print_env(self):
        logger.cli(str(self.session_manager))

    def load(self):
        """Loads the environment"""
        if not self.session_manager.metadata.exists():
            self.session_manager = SessionManager('.')
        else:
            self.session_manager = SessionManager.load()
            logger.cli("Environment file loaded ({})".format(self.session_manager.metadata.abspath))
        logger.cli("environment loaded")
        self.print_env()
        return self.session_manager

    def push_category(self, category):
        """Push all :class:`OperationType` and :class:`Library` in a category"""
        current_env = self.session_manager.current_env
        for protocol in category.list_dirs():
            if protocol.has("source"):
                # then its a Library
                local_lib = current_env.read_library_type(category.name, protocol.name)
                local_lib.code("source").update()
            if protocol.has("protocol"):
                # then its an OperationType
                local_ot = current_env.read_operation_type(category.name, protocol.name)
                for accessor in ['protocol', 'precondition', 'documentation', 'cost_model']:
                    logger.cli("Updating {}/{} ({})".format(category.name, local_ot.name, accessor))
                    code = getattr(local_ot, accessor)
                    code.update()
        self.save()

    def push_all(self):
        """Save protocol"""
        self.check_for_session()
        current_env = self.session_manager.current_env
        categories = current_env.categories
        for cat in categories:
            self.push_category(cat)

    #
    #
    # def fetch_parent_from_server(self, code_file):
    #     code_parent = code_file.code_parent
    #
    #     id_ = {"id": code_parent.id}
    #     aq_code_parents = code_parent.where_callback(code_parent.__class__.__name__, id_)
    #     if aq_code_parents is None or aq_code_parents == []:
    #         logger.warning("Could not find {} with {}".format(
    #             code_parent.__name__, id_))
    #     elif len(aq_code_parents) > 1:
    #         logger.warning("More than one {} found with {}".format(
    #             code_parent.__name__, id_))
    #     else:
    #         return aq_code_parents[0]
    #
    # @staticmethod
    # def get_controller_interface(model_name):
    #     return self.session_manager.current.model_interface(model_name)
    #
    #
    # def fetch_content(self, controller_instance):
    #     """
    #     Fetches code content from Aquarium model (e.g. ot.code('protocol')
    #
    #     :param code_container: Model that contains code
    #     :type code_container: OperationType or Library
    #     :return:
    #     :rtype:
    #     """
    #     for controller, accessor in self.controllers:
    #         if type(controller_instance) is controller:
    #             return controller_instance.code(accessor).content
    #
    #
    # def ok_to_push(self, code_file):
    #     # Check last modified
    #     # modified_at = code_file.abspath.stat().st_mtime
    #     # if code_file.created_at == modified_at:
    #     #     logger.verbose("File has not been modified")
    #     #     return False
    #     fetched_content = code_file.code.content
    #
    #     # Check local changes
    #     local_content = code_file.read('r')
    #     local_changes = compare_content(local_content, fetched_content)
    #     if not local_changes:
    #         logger.verbose("<{}/{}> there are no local changes.".format(
    #             code_file.code_parent.category,
    #             code_file.code_parent.name))
    #         return False
    #
    #     # Check server changes
    #     server_content = self.fetch_content(
    #         self.fetch_parent_from_server(code_file))
    #     server_changes = compare_content(local_content, server_content)
    #     if not server_changes:
    #         logger.verbose("<{}/{}> there are not any differences between local and server.".format(
    #             code_file.code_parent.category,
    #             code_file.code_parent.name))
    #         return False
    #     return True
    #
    #
    # def get_code_files(self):
    #     if not self.session_managerironment().session_dir().exists():
    #         logger.cli("There are no protocols in this repo.")
    #         return []
    #     files = self.session_managerironment().session_dir().files
    #     code_files = [f for f in files if hasattr(f, 'code_parent')]
    #     return code_files

    def session(self):
        """Returns the current session"""
        return self.session_manager.current

    def sessions_json(self):
        """Returns a dictionary of sessions"""
        sess_dict = {}
        for session_name, session in self.session_manager.sessions.items():
            val = str(session)
            sess_dict[session_name] = val
        return sess_dict

    def get_categories(self):
        """Returns dictionary of category names and Library/OperationType"""
        categories = {}
        operation_types = self.session_manager.current.OperationType.all()
        libraries = self.session_manager.current.Library.all()
        for ot in operation_types:
            l = categories.get(ot.category, [])
            l.append(ot)
            categories[ot.category] = l
        for lib in libraries:
            l = categories.get(lib.category, [])
            l.append(lib)
            categories[lib.category] = l
        return categories

    def fetch(self, category):
        """ Fetch protocols from the current session & category and pull to local repo. """
        self.check_for_session()
        ots = self.session_manager.current.OperationType.where({"category": category})
        libs = self.session_manager.current.Library.where({"category": category})
        logger.cli("{} operation_types found".format(len(ots)))
        logger.cli("This may take awhile...")
        for ot in ots:
            logger.cli("Saving {}".format(ot.name))
            curr_env = self.session_manager.current_env
            curr_env.write_operation_type(ot)
        for lib in libs:
            logger.cli("Saving {}".format(lib.name))
            curr_env = self.session_manager.current_env
            curr_env.write_library(lib)
        self.save()

    def sessions(self):
        """List the current available sessions"""
        sessions = self.session_manager.sessions
        logger.cli(format_json(self.sessions_json()))
        return sessions

    # def state(self):
    #     """ Get the current environment state. """
    #     logger.cli(format_json({
    #         "session": "{}: {}".format(
    #             self.session_manager.session_name,
    #             str(self.session_manager.current)),
    #         "sessions": self.sessions_json(),
    #         "category": self.session_manager.category,
    #         "repo": str(self.session_manager.repo.abspath)
    #     }))
    #

    def protocols(self):
        """Print category and protocol names"""
        env = self.session_manager.current_env
        cats = env.protocols.dirs
        for cat in env.protocols.dirs:
            for code in cat.dirs:
                logger.cli(cat.name + "/" + code.name)

    #

    #
    #
    # def protocols(self):
    #     """ Get and count the number of protocols on the local machine """
    #     self.check_for_session()
    #     files = self.get_code_files()
    #     logger.cli(format_json(
    #         ['/'.join([f.code_parent.category, f.code_parent.name]) for f in files]))
    #
    #
    #
    # def category(self):
    #     """ Get the current category of the environment. """
    #     logger.cli(self.session_manager.category)
    #     return self.session_manager.category
    #
    #
    #
    # def set_category(self, category):
    #     """ Set the category of the environment. Set "all" to use all categories. Use "categories" to find all
    #     categories. """
    #     self.check_for_session()
    #     logger.cli("Setting category to \"{}\"".format(category))
    #     self.session_manager.category = category
    #     self.save()


    def categories(self):
        """ Get all available categories and count """
        self.check_for_session()
        logger.cli("Getting category counts:")
        categories = self.get_categories()
        category_count = {k: len(v) for k, v in categories.items()}
        logger.cli(format_json(category_count))

    def set_session(self, session_name):
        """ Set the session by name. Use "sessions" to find all available sessions. """
        sessions = self.session_manager.sessions
        if session_name not in sessions:
            logger.error("Session \"{}\" not in available sessions ({})".format(session_name, ', '
                                                                                              ''.join(sessions.keys())))

        logger.cli("Setting session to \"{}\"".format(session_name))
        self.session_manager.set_current(session_name)
        self.save()

    def set(self, session_name, category):
        """Sets the session and category"""
        self.set_session(session_name)
        self.set_category(category)

    def move_repo(self, path):
        """Moves the current repo to another location."""
        path = Path(path).absolute()
        if not path.is_dir():
            raise Exception("Path {} does not exist".format(str(path)))
        logger.cli("Moving repo location from {} to {}".format(
            self.session_manager.abspath, path))
        self.session_manager.move_repo(path)
        self.save()

    def register(self, login,
                 password,
                 aquarium_url,
                 session_name):
        """Registers a new session."""
        try:
            self.session_manager.register_session(login, password,
                                                  aquarium_url, session_name)
        except InvalidSchema:
            raise InvalidSchema("Missing schema for {}. Did you forget the \"http://\"?"
                                .format(aquarium_url))
        logger.cli("registering session: {}".format(session_name))
        self.save()
        return self

    def unregister(self, name):
        if name in self.session_manager.sessions:
            logger.cli("Unregistering {}: {}".format(
                name, str(self.session_manager.get_session(name))))
            self.session_manager.remove_session(name)
        else:
            logger.cli("Session {} does not exist".format(name))
        self.save()

    #
    # def clear_history(self):
    #     if env_data.exists():
    #         os.remove(env_data.abspath)
    #     logger.cli("Cleared history")

    def ls(self):
        """List dictionary structure for the session manager"""
        logger.cli(str(self.session_manager.abspath))
        logger.cli('\n' + self.session_manager.show())


# TODO: if Parrotfish is updated, make sure there is a way to delete the old environment if somekind of error occurs
def run_pfish():
    # TODO: initialize parrot fish and fire.Fire it
    CustomLogging.set_level(logging.VERBOSE)
    sm = SessionManager('.')
    pf = ParrotFish(sm)
    pf.load()
    fire.Fire(pf)

    # except:
    #     raise Exception("Something went wrong while loading an old environment file."
    #                     "This can happen if there was an update to parrotfish."
    #                     "If you cannot resolve the error, run 'pfish clear_history' in "
    #                     "your counsel to"
    #                     "remove the old file and create a new one.")



if __name__ == '__main__':
    session_manager = SessionManager('.')
    pf = ParrotFish(session_manager)

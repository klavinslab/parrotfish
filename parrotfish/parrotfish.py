import itertools
import os
import re
from os import sep
from pathlib import Path

import hug
import inflection
from hug import API
from parrotfish.utils import compare_content, CustomLogging, logging, format_json, sanitize_filename
from prompt_toolkit import prompt
from prompt_toolkit.contrib.completers import WordCompleter, PathCompleter
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token
from pydent.models import OperationType, Library
from requests.exceptions import InvalidSchema
from parrotfish.session_environment import SessionManager

logger = CustomLogging.get_logger(__name__)
API = hug.API('parrotfish')
EXIT = -1

prompt_style = style_from_dict({
    # User input.
    Token: '#ff0066',

    # Prompt.
    Token.Username: '#884444 italic',
    Token.At: '#00aa00',
    Token.Colon: '#00aa00',
    Token.Pound: '#00aa00',
    Token.Host: '#000088 bg:#aaaaff',
    Token.Path: '#884444 underline',

    # Make a selection reverse/underlined.
    # (Use Control-Space to select.)
    Token.SelectedText: 'reverse underline',
    Token.Toolbar: '#ffffff bg:#333333',
})


# def get_prompt_tokens(cli):
#     login = '<not logged in>'
#     url = '<???>'
#
#     if self.session_manager.current:
#         login = self.session_manager.current.login
#         url = self.session_manager.current.url
#
#     return [
#         (Token.Username, login),
#         (Token.At, '@'),
#         (Token.Host, url),
#         (Token.Colon, ':'),
#         (Token.Pound, '{}'.format(self.session_manager.session_name)),
#         (Token.Pound, '#{} '.format(self.session_manager.category)),
#     ]
#

class CustomCompleter(WordCompleter):
    """
    Matches commands only at current text position.
    """

    def __init__(self, words, ignore_case=False, meta_dict=None, match_middle=False):
        super().__init__(words, ignore_case=ignore_case, WORD=False, meta_dict=meta_dict, sentence=True,
                         match_middle=match_middle)

    def get_completions(self, document, complete_event):
        """Override completion method that retrieves only completions whose length less than or equal
        to the current completion text. This eliminates excessivlely long completion lists"""

        get_words = lambda text: re.split('\s+', text)
        completions = list(super().get_completions(document, complete_event))

        # filter completions by length of word
        text_before_cursor = document.text_before_cursor
        words_before_cursor = get_words(text_before_cursor)
        for c in completions:
            cwords = get_words(c.text)
            if len(cwords) <= len(words_before_cursor):
                yield c


@hug.object(name='parrotfish', version='1.0.0', api=API)
class ParrotFish(object):
    """Contains command and methods for updating and pushing protocols from Aquarium. Automatically
    exposes commands to the command line interface (CLI) using _Hug.

    .. _Hug: http://www.hug.rest/
    """

    controllers = [
        (OperationType, "protocol"),
        (Library, "source")
    ]

    def __init__(self):
        """
        ParrotFish constructor
        """
        self.session_manager = SessionManager()

    def add_session_manager(self, new_sm):
        self.session_manager = new_sm

    def check_for_session(self):
        if self.session_manager.current is None:
            raise Exception(
                "You must be logged in. Register an Aquarium session.")

    
    def save(self):
        """Saves the environment"""
        self.session_manager.save()

    @classmethod
    def load(self):
        """Loads the environment"""
        if not self.session_manager.metadata.exists():
            self.session_manager = SessionManager()
        else:
            self.session_manager = SessionManager(self.session_manager)
            self.session_manager.load()
        return self.session_manager

    # 
    # @hug.object.cli
    # def push(self):
    #     self.check_for_session()
    #     code_files = self.get_code_files()
    #
    #     if not self.session_manager.use_all_categories():
    #         code_files = [
    #             f for f in code_files if f.code_parent.category == self.session_manager.category]
    #
    #     for c in code_files:
    #         if self.ok_to_push(c):
    #             c.code.content = c.read('r')
    #             c.code.update()
    #             # pass
    #     self.save()
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

    
    @hug.object.cli
    def session(self):
        return self.session_manager.current

    
    def sessions_json(self):
        sess_dict = {}
        for session_name, session in self.session_manager.sessions.items():
            val = str(session)
            sess_dict[session_name] = val
        return sess_dict

    
    def get_categories(self):
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

    
    @hug.object.cli
    def fetch(self, category: hug.types.text):
        """ Fetch protocols from the current session & category and pull to local repo. """
        self.check_for_session()
        ots = self.session_manager.current.OperationType.where({"category": category})
        logger.cli("{} operation_types found".format(len(ots)))
        logger.cli("This may take awhile...")
        for ot in ots:
            print(ot)
            logger.cli("Saving {}".format(ot.name))
            curr_env = self.session_manager.current_env
            curr_env.write_operation_type(ot)
        self.save()

    
    @hug.object.cli
    def sessions(self):
        """List the current available sessions"""
        sessions = self.session_manager.sessions
        logger.cli(format_json(self.sessions_json()))
        return sessions

    # 
    # @hug.object.cli
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

    
    @hug.object.cli
    def protocols(self):
        env = self.session_manager.current_env
        cats = env.protocols.dirs
        for cat in env.protocols.dirs:
            for code in cat.dirs:
                logger.cli(cat.name + "/" + code.name)

    #

    # 
    # @hug.object.cli
    # def protocols(self):
    #     """ Get and count the number of protocols on the local machine """
    #     self.check_for_session()
    #     files = self.get_code_files()
    #     logger.cli(format_json(
    #         ['/'.join([f.code_parent.category, f.code_parent.name]) for f in files]))
    #
    # 
    # @hug.object.cli
    # def category(self):
    #     """ Get the current category of the environment. """
    #     logger.cli(self.session_manager.category)
    #     return self.session_manager.category
    #
    # 
    # @hug.object.cli
    # def set_category(self, category: hug.types.text):
    #     """ Set the category of the environment. Set "all" to use all categories. Use "categories" to find all
    #     categories. """
    #     self.check_for_session()
    #     logger.cli("Setting category to \"{}\"".format(category))
    #     self.session_manager.category = category
    #     self.save()

    
    @hug.object.cli
    def categories(self):
        """ Get all available categories and count """
        self.check_for_session()
        logger.cli("Getting category counts:")
        categories = self.get_categories()
        category_count = {k: len(v) for k, v in categories.items()}
        logger.cli(format_json(category_count))

    
    @hug.object.cli
    def set_session(self, session_name: hug.types.text):
        """ Set the session by name. Use "sessions" to find all available sessions. """
        sessions = self.session_manager.sessions
        if session_name not in sessions:
            logger.error("Session \"{}\" not in available sessions ({})".format(session_name, ', '
                                                                                              ''.join(sessions.keys())))

        logger.cli("Setting session to \"{}\"".format(session_name))
        self.session_manager.set_current(session_name)
        self.save()

    
    @hug.object.cli
    def set(self, session_name: hug.types.text, category: hug.types.text):
        """Sets the session and category"""
        self.set_session(session_name)
        self.set_category(category)

    
    @hug.object.cli
    def move_repo(self, path: hug.types.text):
        """ Moves the current repo to another location. """
        path = Path(path).absolute()
        if not path.is_dir():
            raise Exception("Path {} does not exist".format(str(path)))
        logger.cli("Moving repo location from {} to {}".format(
            self.session_manager.abspath, path))
        self.session_manager.move_repo(path)
        self.save()

    
    @hug.object.cli
    def register(self, login: hug.types.text,
                 password: hug.types.text,
                 aquarium_url: hug.types.text,
                 session_name: hug.types.text):
        """ Registers a new session. """
        try:
            self.session_manager.register_session(login, password,
                                aquarium_url, session_name)
        except InvalidSchema:
            raise InvalidSchema("Missing schema for {}. Did you forget the \"http://\"?"
                                .format(aquarium_url))
        logger.cli("registering session: {}".format(session_name))
        self.save()
        return self

    
    @hug.object.cli
    def unregister(self, name):
        if name in self.session_manager.sessions:
            logger.cli("Unregistering {}: {}".format(
                name, str(self.session_manager.get_session(name))))
            self.session_manager.remove_session(name)
        else:
            logger.cli("Session {} does not exist".format(name))
        self.save()

    # @hug.object.cli
    # def clear_history(self):
    #     if env_data.exists():
    #         os.remove(env_data.abspath)
    #     logger.cli("Cleared history")

    
    @hug.object.cli
    def ls(self):
        logger.cli(str(self.session_manager.abspath))
        logger.cli('\n' + self.session_manager.show())

    ####################################
    ########  Shell Methods  ###########
    ####################################

    
    def command_completer(self):
        def add_completions(*iterables):
            words = []
            products = itertools.product(*iterables)
            for prod in products:
                for i, word in enumerate(prod):
                    partial_prod = prod[:i + 1]
                    words.append(' '.join(partial_prod))
            return list(set(words))

        completions = []
        if self.session_manager.current:
            categories = list(self.get_categories().keys())
            completions += add_completions(['set_category'], categories)
        if self.session_manager.sessions:
            completions += add_completions(['set_session'], self.session_manager.sessions.keys())
        completions += ["exit"]
        completions += list(API.cli.commands.keys())
        return CustomCompleter(list(set(completions)))

    def parse_shell_command(self, command):
        args = re.split('\s+', command)
        fxn_name = args[0]
        args = args[1:]
        kwargs = {}
        if fxn_name == '-h' or fxn_name == '--help':
            print(API.cli)
        elif fxn_name.startswith('exit'):
            return EXIT
        cmd = API.cli.commands.get(fxn_name, None)
        if cmd:
            if args and args[0] in ['-h', '--help']:
                print(cmd.interface.__doc__)
            else:
                if hasattr(self, '{}_interactive'.format(fxn_name)):
                    args, kwargs = getattr(self, '{}_interactive'.format(fxn_name))()
                try:
                    return cmd.interface(*args, **kwargs)
                except Exception as e:
                    logger.cli(str(e.args))
        elif fxn_name.strip() == '':
            pass
        else:
            print("Cmd {} not found. Use '-h' or '--help' for help. Click tab for available commands.".format(fxn_name))

    def move_repo_interactive(self):
        path = prompt('> enter path: ', completer=PathCompleter(only_directories=True, expanduser=True))
        return (os.path.expanduser(path),), {}

    @hug.object.cli
    def shell(self):
        print("Entering interactive")
        res = 1
        while not res == EXIT:
            def get_bottom_toolbar_tokens(cli):
                # return [(Token.Toolbar, ' \'-h\' or \'--help\' for help | \'exit\' to exit')]
                return [(Token.Toolbar, 'Dir: {}'.format(str(self.session_manager.repo.abspath)))]

            answer = prompt(completer=self.command_completer(),
                            get_prompt_tokens=get_prompt_tokens,
                            style=prompt_style,
                            get_bottom_toolbar_tokens=get_bottom_toolbar_tokens)
            res = self.parse_shell_command(answer)
        print("goodbye!")


# TODO: if Parrotfish is updated, make sure there is a way to delete the old environment if somekind of error occurs
def run_pfish():
    print(os.getcwd())
    try:
        ParrotFish.load()
    except:
        raise Exception("Something went wrong while loading an old environment file."
                        "This can happen if there was an update to parrotfish."
                        "If you cannot resolve the error, run 'pfish clear_history' in "
                        "your counsel to"
                        "remove the old file and create a new one.")
    CustomLogging.set_level(logging.VERBOSE)
    API.cli()


if __name__ == '__main__':
    run_pfish()

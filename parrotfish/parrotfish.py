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
from parrotfish.session_environment import SessionManager, env_data

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


def get_prompt_tokens(cli):
    login = '<not logged in>'
    url = '<???>'

    if Env.current:
        login = Env.current.login
        url = Env.current.url

    return [
        (Token.Username, login),
        (Token.At, '@'),
        (Token.Host, url),
        (Token.Colon, ':'),
        (Token.Pound, '{}'.format(Env.session_name)),
        (Token.Pound, '#{} '.format(Env.category)),
    ]


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

    # Aliases
    Env = SessionManager()

    @classmethod
    def check_for_session(cls):
        if cls.Env.current is None:
            raise Exception(
                "You must be logged in. Register an Aquarium session.")

    @classmethod
    def save(cls):
        """Saves the environment"""
        cls.Env.save()

    @classmethod
    def load(cls):
        """Loads the environment"""
        if not env_data.env.exists():
            cls.Env = SessionManager()
        else:
            cls.Env = SessionManager.load()
        return cls.Env

    # @classmethod
    # @hug.object.cli
    # def push(cls):
    #     cls.check_for_session()
    #     code_files = cls.get_code_files()
    #
    #     if not Env.use_all_categories():
    #         code_files = [
    #             f for f in code_files if f.code_parent.category == Env.category]
    #
    #     for c in code_files:
    #         if cls.ok_to_push(c):
    #             c.code.content = c.read('r')
    #             c.code.update()
    #             # pass
    #     cls.save()
    #
    # @classmethod
    # def fetch_parent_from_server(cls, code_file):
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
    #     return Env.current.model_interface(model_name)
    #
    # @classmethod
    # def fetch_content(cls, controller_instance):
    #     """
    #     Fetches code content from Aquarium model (e.g. ot.code('protocol')
    #
    #     :param code_container: Model that contains code
    #     :type code_container: OperationType or Library
    #     :return:
    #     :rtype:
    #     """
    #     for controller, accessor in cls.controllers:
    #         if type(controller_instance) is controller:
    #             return controller_instance.code(accessor).content
    #
    # @classmethod
    # def ok_to_push(cls, code_file):
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
    #     server_content = cls.fetch_content(
    #         cls.fetch_parent_from_server(code_file))
    #     server_changes = compare_content(local_content, server_content)
    #     if not server_changes:
    #         logger.verbose("<{}/{}> there are not any differences between local and server.".format(
    #             code_file.code_parent.category,
    #             code_file.code_parent.name))
    #         return False
    #     return True
    #
    # @classmethod
    # def get_code_files(cls):
    #     if not Environment().session_dir().exists():
    #         logger.cli("There are no protocols in this repo.")
    #         return []
    #     files = Environment().session_dir().files
    #     code_files = [f for f in files if hasattr(f, 'code_parent')]
    #     return code_files

    @classmethod
    def sessions_json(cls):
        sess_dict = {}
        for session in cls.Env.sessions:
            val = str(session)
            if session is cls.Env.current:
                val = "**" + str(val) + "**"
            sess_dict[session.name] = session
        return sess_dict

    @classmethod
    def get_categories(cls):
        categories = {}
        for controller, _ in cls.controllers:
            all_models = Env.current.model_interface(controller.__name__).all()
            for m in all_models:
                categories.setdefault(m.category, []).append(m)
        return categories

    @classmethod
    @hug.object.cli
    def fetch(cls):
        """ Fetch protocols from the current session & category and pull to local repo. """
        cls.check_for_session()
        for controller, accessor in cls.controllers:

            # Get models based on category
            model_contoller = cls.get_controller_interface(controller.__name__)
            models = None
            if Environment().use_all_categories():
                models = model_contoller.all()
                logger.cli("Fetching all categories...")
            else:
                models = model_contoller.where({"category": Environment().category})
                logger.cli("Fetching code for category {}".format(
                    Environment().category))
            logger.cli("\t{} {} found...".format(
                len(models), inflection.pluralize(controller.__name__)))

            for m in models:
                logger.cli("\t\tSaving code for {}/{}".format(m.category, m.name))
                code = m.code(accessor)  # an Aquarium Code model
                if code is None:
                    logger.warning("\t\tCould not get code content for {}".format(m.name))
                else:
                    # save code content
                    cat_dir = Environment().get_category(m.category)
                    code_name = '{}.rb'.format(m.name)

                    # sanitize the filename if protocol name has filepath seperators in it
                    if sep in code_name:
                        code_name = sanitize_filename(code_name)

                    # create a MagicFile instance that store the filepath & content
                    code_file = cat_dir.add_file(code_name, make_attr=False, push_up=False)

                    # write the content to the filepath
                    code_file.write('w', code.content)

                    # add additional code_parent information to the MagicFile instance
                    code_file.code = code
                    code_file.code_parent = m
                    code_file.created_at = code_file.abspath.stat().st_mtime
        cls.save()

    @classmethod
    @hug.object.cli
    def sessions(cls):
        """List the current available sessions"""
        sessions = Env.sessions
        logger.cli(format_json(cls.sessions_json()))
        return sessions

    @classmethod
    @hug.object.cli
    def state(cls):
        """ Get the current environment state. """
        logger.cli(format_json({
            "session": "{}: {}".format(
                Env.session_name,
                str(Env.current)),
            "sessions": cls.sessions_json(),
            "category": Env.category,
            "repo": str(Env.repo.abspath)
        }))

    @classmethod
    @hug.object.cli
    def protocols(cls):
        """ Get and count the number of protocols on the local machine """
        cls.check_for_session()
        files = cls.get_code_files()
        logger.cli(format_json(
            ['/'.join([f.code_parent.category, f.code_parent.name]) for f in files]))

    @classmethod
    @hug.object.cli
    def category(cls):
        """ Get the current category of the environment. """
        logger.cli(Env.category)
        return Env.category

    @classmethod
    @hug.object.cli
    def set_category(cls, category: hug.types.text):
        """ Set the category of the environment. Set "all" to use all categories. Use "categories" to find all
        categories. """
        cls.check_for_session()
        logger.cli("Setting category to \"{}\"".format(category))
        Env.category = category
        cls.save()

    @classmethod
    @hug.object.cli
    def categories(cls):
        """ Get all available categories and count """
        cls.check_for_session()
        logger.cli("Getting category counts:")
        categories = cls.get_categories()
        category_count = {k: len(v) for k, v in categories.items()}
        logger.cli(format_json(category_count))

    @classmethod
    @hug.object.cli
    def set_session(cls, session_name: hug.types.text):
        """ Set the session by name. Use "sessions" to find all available sessions. """
        cls.check_for_session()
        sessions = Env.sessions
        if session_name not in sessions:
            logger.error("Session \"{}\" not in available sessions ({})".format(session_name, ', '
                                                                                              ''.join(sessions.keys())))

        logger.cli("Setting session to \"{}\"".format(session_name))
        Env.set_current(session_name)
        cls.save()

    @classmethod
    @hug.object.cli
    def set(cls, session_name: hug.types.text, category: hug.types.text):
        """Sets the session and category"""
        cls.set_session(session_name)
        cls.set_category(category)

    @classmethod
    @hug.object.cli
    def move_repo(cls, path: hug.types.text):
        """ Moves the current repo to another location. """
        path = Path(path).absolute()
        if not path.is_dir():
            raise Exception("Path {} does not exist".format(str(path)))
        logger.cli("Moving repo location from {} to {}".format(
            Env.repo.abspath, path))
        Env.mvdirs(path)
        cls.save()

    @classmethod
    @hug.object.cli
    def register(cls, login: hug.types.text,
                 password: hug.types.text,
                 aquarium_url: hug.types.text,
                 session_name: hug.types.text):
        """ Registers a new session. """
        try:
            cls.Env.register_session(login, password,
                                aquarium_url, session_name)
        except InvalidSchema:
            raise InvalidSchema("Missing schema for {}. Did you forget the \"http://\"?"
                                .format(aquarium_url))
        logger.cli("registering session: {}".format(session_name))
        cls.save()
        return cls

    @classmethod
    @hug.object.cli
    def unregister(cls, name):
        if name in cls.Env.sessions:
            logger.cli("Unregistering {}: {}".format(
                name, str(Env.get_session(name))))
            cls.Env.remove_session(name)
        else:
            logger.cli("Session {} does not exist".format(name))
        cls.save()

    # @hug.object.cli
    # def clear_history(self):
    #     if env_data.exists():
    #         os.remove(env_data.abspath)
    #     logger.cli("Cleared history")

    @classmethod
    @hug.object.cli
    def ls(cls):
        logger.cli(str(Env.abspath))
        logger.cli('\n' + Env.repo.show())

    ####################################
    ########  Shell Methods  ###########
    ####################################

    @classmethod
    def command_completer(cls):
        def add_completions(*iterables):
            words = []
            products = itertools.product(*iterables)
            for prod in products:
                for i, word in enumerate(prod):
                    partial_prod = prod[:i + 1]
                    words.append(' '.join(partial_prod))
            return list(set(words))

        completions = []
        if Env.current:
            categories = list(cls.get_categories().keys())
            completions += add_completions(['set_category'], categories)
        if Env.sessions:
            completions += add_completions(['set_session'], Env.sessions.keys())
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
                return [(Token.Toolbar, 'Dir: {}'.format(str(Env.repo.abspath)))]

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

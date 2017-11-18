import hug
from hug import API
from parrotfish.environment import Environment
from parrotfish.utils import compare_content, CustomLogging, logging, format_json, sanitize_filename
from requests.exceptions import InvalidSchema
from pathlib import Path
import inflection
from os import sep
from pydent.models import OperationType, Library

import hug
from prompt_toolkit.shortcuts import prompt, confirm
from prompt_toolkit.contrib.completers import WordCompleter
import re
from prompt_toolkit import prompt
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token
import os


logger = CustomLogging.get_logger(__name__)
API = hug.API('parrotfish')

# Aliases
Env = Environment()
SM = Env.session_manager


example_style = style_from_dict({
    # User input.
    Token:          '#ff0066',

    # Prompt.
    Token.Username: '#884444 italic',
    Token.At:       '#00aa00',
    Token.Colon:    '#00aa00',
    Token.Pound:    '#00aa00',
    Token.Host:     '#000088 bg:#aaaaff',
    Token.Path:     '#884444 underline',

    # Make a selection reverse/underlined.
    # (Use Control-Space to select.)
    Token.SelectedText: 'reverse underline',
})


def get_prompt_tokens(cli):
    login = '<not logged in>'
    url = '<???>'

    if SM.current:
        login = SM.current.login
        url = SM.current.url

    return [
        (Token.Username, login),
        (Token.At,       '@'),
        (Token.Host,     url),
        (Token.Colon,    ':'),
        (Token.Pound,    '#{} '.format(Env.category)),
    ]



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

    @classmethod
    def check_for_session(cls):
        if SM.current is None:
            raise Exception(
                "You must be logged in. Register an Aquarium session.")

    @staticmethod
    def save():
        """Saves the environment"""
        Env.save()

    @staticmethod
    def load():
        """Loads the environment"""
        Env.load()

    @classmethod
    @hug.object.cli
    def push(cls):
        cls.check_for_session()
        code_files = cls.get_code_files()

        if not Env.use_all_categories():
            code_files = [
                f for f in code_files if f.code_parent.category == Env.category]

        for c in code_files:
            if cls.ok_to_push(c):
                c.code.content = c.read('r')
                c.code.update()
                # pass
        cls.save()


    ############################
    #####  Code Managment  #####
    ############################

    @classmethod
    def fetch_parent_from_server(cls, code_file):
        code_parent = code_file.code_parent

        id_ = {"id": code_parent.id}
        aq_code_parents = code_parent.where(code_parent.__class__.__name__, id_)
        if aq_code_parents is None or aq_code_parents == []:
            logger.warning("Could not find {} with {}".format(
                code_parent.__name__, id_))
        elif len(aq_code_parents) > 1:
            logger.warning("More than one {} found with {}".format(
                code_parent.__name__, id_))
        else:
            return aq_code_parents[0]

    @staticmethod
    def get_controller_interface(model_name):
        return SM.current.model_interface(model_name)

    @classmethod
    def fetch_content(cls, controller_instance):
        """
        Fetches code content from Aquarium model (e.g. ot.code('protocol')

        :param code_container: Model that contains code
        :type code_container: OperationType or Library
        :return:
        :rtype:
        """
        for controller, accessor in cls.controllers:
            if type(controller_instance) is controller:
                return controller_instance.code(accessor).content

    @classmethod
    def ok_to_push(cls, code_file):
        # Check last modified
        # modified_at = code_file.abspath.stat().st_mtime
        # if code_file.created_at == modified_at:
        #     logger.verbose("File has not been modified")
        #     return False
        fetched_content = code_file.code.content

        # Check local changes
        local_content = code_file.read('r')
        local_changes = compare_content(local_content, fetched_content)
        if not local_changes:
            logger.verbose("<{}/{}> there are no local changes.".format(
                code_file.code_parent.category,
                code_file.code_parent.name))
            return False

        # Check server changes
        server_content = cls.fetch_content(
            cls.fetch_parent_from_server(code_file))
        server_changes = compare_content(local_content, server_content)
        if not server_changes:
            logger.verbose("<{}/{}> there are not any differences between local and server.".format(
                code_file.code_parent.category,
                code_file.code_parent.name))
            return False
        return True

    @classmethod
    def get_code_files(cls):
        if not Environment().session_dir().exists():
            logger.cli("There are no protocols in this repo.")
            return []
        files = Environment().session_dir().files
        code_files = [f for f in files if hasattr(f, 'code_parent')]
        return code_files


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
    def sessions_json(cls):
        sess_dict = {}
        for key, val in SM.sessions.items():
            val = str(val)
            if val is SM.current:
                val = "**" + str(val) + "**"
            sess_dict[key] = val
        return sess_dict

    @classmethod
    @hug.object.cli
    def sessions(cls):
        """List the current available sessions"""
        sessions = SM.sessions
        logger.cli(format_json(cls.sessions_json()))
        return sessions

    @classmethod
    @hug.object.cli
    def state(cls):
        """ Get the current environment state. """
        logger.cli(format_json({
            "session": "{}: {}".format(
                SM.session_name,
                str(SM.current)),
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
        categories = {}
        for controller, _ in cls.controllers:
            for m in controller.all():
                categories.setdefault(m.category, []).append(m)
        category_count = {k: len(v) for k, v in categories.items()}
        logger.cli(format_json(category_count))

    @classmethod
    @hug.object.cli
    def set_session(cls, session_name: hug.types.text):
        """ Set the session by name. Use "sessions" to find all available sessions. """
        cls.check_for_session()
        sessions = SM.sessions
        if session_name not in sessions:
            logger.error("Session \"{}\" not in available sessions ({})".format(session_name, ', '
                                                                                              ''.join(sessions.keys())))

        logger.cli("Setting session to \"{}\"".format(session_name))
        SM.set(session_name)
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
        Env.repo.mvdirs(path)
        cls.save()

    @classmethod
    @hug.object.cli
    def register(cls, login: hug.types.text,
                 password: hug.types.text,
                 aquarium_url: hug.types.text,
                 session_name: hug.types.text):
        """ Registers a new session. """
        try:
            SM.register_session(login, password,
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
        sessions = SM
        if name in sessions:
            logger.cli("Unregistering {}: {}".format(
                name, str(sessions[name])))
            sessions.remove_session(name)
        else:
            logger.cli("Session {} does not exist".format(name))
        cls.save()

    @hug.object.cli
    def clear_history(self):
        env_pkl = Env.env_pkl()
        if env_pkl.exists():
            os.remove(env_pkl)
        logger.cli("Cleared history")



    @hug.object.cli
    def exit(self, interactive=True):
        return -1

    def command_completer(self):
        return WordCompleter(list(API.cli.commands.keys()))


    # TODO: create interactive wrapper for sending parameters to other commands
    # TODO: word completer for specific commands
    @hug.object.cli
    def interactive(self):
        print("Entering interactive")
        res = 1
        while not res == -1:
            answer = prompt(completer=self.command_completer(),
                            get_prompt_tokens=get_prompt_tokens,
                            style=example_style)
            args = re.split('\s+', answer)
            fxn_name = args[0]
            args = args[1:]
            if fxn_name in API.cli.commands:
                fxn = getattr(self, fxn_name)
                res = fxn(*args, interactive=True)
            elif fxn_name == '-h' or fxn_name == '--h':
                print(API._cli)
            else:
                print("Cmd {} not found. Use '-h' or '--help' for help. Click tab for available cmds.".format(fxn_name))

        print("goodbye!")


# TODO: if Parrotfish is updated, make sure there is a way to delete the old environment if somekind of error occurs

def run_pfish():
    ParrotFish.load()
    CustomLogging.set_level(logging.VERBOSE)
    API.cli()

if __name__ == '__main__':
    run_pfish()
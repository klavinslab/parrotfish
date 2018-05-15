"""
Interactive shell
"""

import itertools
import os
import re

import fire
from parrotfish.utils import CustomLogging, get_callables
from prompt_toolkit import prompt
from prompt_toolkit.contrib.completers import WordCompleter, PathCompleter
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token

logger = CustomLogging.get_logger(__name__)


class CustomCompleter(WordCompleter):
    """
    Matches commands only at current text position.
    """

    def __init__(self, words, ignore_case=False, meta_dict=None,
                 match_middle=False):
        super().__init__(words, ignore_case=ignore_case, WORD=False,
                         meta_dict=meta_dict, sentence=True,
                         match_middle=match_middle)

    def get_completions(self, document, complete_event):
        """
        Override completion method that retrieves only completions whose
        length less than or equal to the current completion text.
        This eliminates excessivlely long completion lists
        """

        def get_words(text): return re.split('\\s+', text)
        completions = list(super().get_completions(document, complete_event))

        # filter completions by length of word
        text_before_cursor = document.text_before_cursor
        words_before_cursor = get_words(text_before_cursor)
        for c in completions:
            cwords = get_words(c.text)
            if len(cwords) <= len(words_before_cursor):
                yield c


class Shell(object):

    PROMPT_STYLE = style_from_dict({
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

    EXIT = -1

    def __init__(self, cli_instance):
        self.cli = cli_instance

    @property
    def commands(self):
        return get_callables(self.cli.__class__)

    def command_completer(self):
        def add_completions(*iterables):
            words = []
            products = itertools.product(*iterables)
            for prod in products:
                for i, _word in enumerate(prod):
                    partial_prod = prod[:i + 1]
                    words.append(' '.join(partial_prod))
            return list(set(words))

        completions = []
        if self.cli._session_manager.current_session:
            categories = list(self.cli._get_categories().keys())
            completions += add_completions(['fetch'], categories)
            completions += add_completions(['push_category'], categories)
        if self.cli._session_manager.sessions:
            completions += add_completions(
                ['set_session'],
                self.cli._session_manager.sessions.keys())
        completions += ["exit"]
        completions += self.commands
        return CustomCompleter(list(set(completions)))

    def parse_shell_command(self, command):
        args = re.split('\\s+', command)
        fxn_name = args[0]
        args = args[1:]
        kwargs = {}
        if fxn_name == '-h' or fxn_name == '--help':
            fire.Fire(self.cli, command='{} -- --help'.format(fxn_name))
        elif fxn_name.startswith('exit'):
            return self.EXIT
        cmd = getattr(self.cli, fxn_name, None)
        if cmd:
            if args and args[0] in ['-h', '--help']:
                print(cmd.interface.__doc__)
            else:
                if hasattr(self, '{}_interactive'.format(fxn_name)):
                    args, kwargs = getattr(
                        self, '{}_interactive'.format(fxn_name))()
                try:
                    return cmd(*args, **kwargs)
                except Exception as e:
                    logger.cli(str(e.args))
        elif fxn_name.strip() == '':
            pass
        else:
            print("Cmd {} not found. Use '-h' or '--help' for help. Click tab for available commands.".format(fxn_name))

    # TODO: Probably a better way to do this...
    @staticmethod
    def set_repo_interactive():
        return Shell.get_path()

    @staticmethod
    def move_repo_interactive():
        return Shell.get_path()

    @staticmethod
    def get_path():
        path = prompt('> enter path: ', completer=PathCompleter(
            only_directories=True, expanduser=True))
        return (os.path.expanduser(path),), {}

    def run(self):
        print("Entering interactive")
        res = 1
        while not res == self.EXIT:
            def get_bottom_toolbar_tokens(cli):
                return [(Token.Toolbar,
                         'Dir: {}'.format(
                             str(self.cli._session_manager.abspath)))]

            answer = prompt(completer=self.command_completer(),
                            get_prompt_tokens=self.get_prompt_tokens,
                            style=self.PROMPT_STYLE,
                            get_bottom_toolbar_tokens=get_bottom_toolbar_tokens)
            res = self.parse_shell_command(answer)
        print("goodbye!")

    def get_prompt_tokens(self, ljk):
        login = '<not logged in>'
        url = '<???>'
        name = '<NO SESSION>'
        if self.cli._session_manager.current_session:
            login = self.cli._session_manager.current_session.login
            url = self.cli._session_manager.current_session.url
            name = self.cli._session_manager.current_session.name

        return [
            (Token.Username, login),
            (Token.At, '@'),
            (Token.Host, url),
            (Token.Colon, ':'),
            (Token.Pound, '{}'.format(name + ": "))
        ]

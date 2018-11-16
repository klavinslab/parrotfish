"""
Interactive shell
"""

import itertools
import os
import re

import fire
from parrotfish.utils import CustomLogging, get_callables
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter, PathCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML

logger = CustomLogging.get_logger(__name__)


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


class Shell(object):

    PROMPT_STYLE = Style.from_dict({
        # User input.
        '': '#ff0066',

        # Prompt.
        'username': '#884444 italic',
        'at': '#00aa00',
        'colon': '#00aa00',
        'pound': '#00aa00',
        'host': '#000088 bg:#aaaaff',
        'path': '#884444 underline',
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
                for i, word in enumerate(prod):
                    partial_prod = prod[:i + 1]
                    words.append(' '.join(partial_prod))
            return list(set(words))

        completions = []
        if self.cli._session_manager.current_session:
            categories = list(self.cli._get_categories().keys())
            completions += add_completions(['fetch'], categories)
            completions += add_completions(['push'], categories)
        if self.cli._session_manager.sessions:
            completions += add_completions(['set_session'], self.cli._session_manager.sessions.keys())
        completions += ["exit"]
        completions += self.commands
        return CustomCompleter(list(set(completions)))

    def parse_shell_command(self, command):
        args = re.split('\s+', command)
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
                    args, kwargs = getattr(self, '{}_interactive'.format(fxn_name))()
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
        path = prompt('> enter path: ', completer=PathCompleter(only_directories=True, expanduser=True))
        return (os.path.expanduser(path),), {}

    def run(self):
        print("Entering interactive")
        res = 1
        while not res == self.EXIT:
            answer = prompt(self.get_prompt_tokens(),
                            completer=self.command_completer(),
                            style=self.PROMPT_STYLE,
                            bottom_toolbar=self.bottom_toolbar)
            res = self.parse_shell_command(answer)
        print("goodbye!")

    def bottom_toolbar(self):
        return HTML('DIR: {}'.format(str(self.cli._session_manager.abspath)))

    def get_prompt_tokens(self):
        login = '<not logged in>'
        url = '<???>'
        name = '<NO SESSION>'
        if self.cli._session_manager.current_session:
            login = self.cli._session_manager.current_session.login
            url = self.cli._session_manager.current_session.url
            name = self.cli._session_manager.current_session.name

        return [
            ('class:username', login),
            ('class:at', '@'),
            ('class:host', url),
            ('class:color', ':'),
            ('class:pound', '{}'.format(name + ": "))
        ]


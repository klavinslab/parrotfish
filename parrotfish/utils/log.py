"""
Custom logging functions
"""

import logging

try:
    from colorama import Fore, Back, Style, init
    init()
except ImportError:  # fallback so that the imported classes always exist
    class ColorFallback():
        def __getattr__(self, name): return ''
    Fore = Back = Style = ColorFallback()

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.WARNING)


class CustomLogging(object):
    log_level = logging.WARNING
    children = []

    @staticmethod
    def add_log_function(level_name, level, color=None):
        setattr(logging, level_name.upper(), level_name.upper())
        logging.addLevelName(level, level_name.upper())

        def custom_log(self, message, *args, **kws):
            # Yes, logger takes its '*args' as 'args'.
            if self.isEnabledFor(level):
                if not color is None:
                    message = color + message + Fore.RESET
                self._log(level, message, args, **kws)

        setattr(logging.Logger, level_name.lower(), custom_log)

    @classmethod
    def set_level(cls, level):
        cls.log_level = level
        [c.setLevel(level) for c in cls.children]

    @classmethod
    def get_logger(cls, name):
        logger = logging.getLogger(name)
        logger.setLevel(cls.log_level)
        cls.children.append(logger)
        return logger


CustomLogging.add_log_function("VERBOSE", 21, color=Fore.LIGHTMAGENTA_EX)
CustomLogging.add_log_function("CLI", 29, color=Fore.BLUE)

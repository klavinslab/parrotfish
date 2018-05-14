"""
Utility functions for comparing two large strings.

credit: https://chezsoi.org/lucas/blog/colored-diff-output-with-python.html
"""
import difflib

try:
    from colorama import Fore, Back, Style, init
    init()
except ImportError:  # fallback so that the imported classes always exist
    class ColorFallback():
        def __getattr__(self, name): return ''
    Fore = Back = Style = ColorFallback()


def color_diff(diff):
    for line in diff:
        if line.startswith('+'):
            yield Fore.GREEN + line + Fore.RESET
        elif line.startswith('-'):
            yield Fore.RED + line + Fore.RESET
        elif line.startswith('^'):
            yield Fore.BLUE + line + Fore.RESET
        elif line.startswith('?'):
            yield Fore.CYAN + line + Fore.RESET
        else:
            yield line


def compare_content(content1, content2):
    lines1 = content1.split('\n')
    lines2 = content2.split('\n')
    diff = color_diff(difflib.unified_diff(lines1, lines2))
    return ''.join(diff)

import os
import re
from distutils.core import setup


tests_require = [
    'pytest',
    'pytest-runner',
    'python-coveralls',
    'pytest-pep8'
]

install_requires = [
    'pydent',
    'dill',
    'opath',
    'colorama',
    'prompt_toolkit',
    'cryptography',
    'fire',
]

classifiers = [],

# setup functions

def sanitize_string(str):
    str = str.replace('\"', '')
    str = str.replace("\'", '')
    return str


def parse_version_file():
    """Parse the __version__.py file"""
    here = os.path.abspath(os.path.dirname(__file__))
    ver_dict = {}
    with open(os.path.join(here, 'parrotfish', '__version__.py'), 'r') as f:
        for line in f.readlines():
            m = re.match('__(\w+)__\s*=\s*(.+)', line)
            if m:
                ver_dict[m.group(1)] = sanitize_string(m.group(2))
    return ver_dict


def read(fname):
    """Read a file"""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

ver = parse_version_file()

# setup
setup(
    name=ver['title'],
    version=ver['version'],
    packages=['parrotfish', 'parrotfish.utils'],
    package_data={
        'parrotfish': ['.environ', 'data']
    },
    url='https://github.com/klavinslab/parrotfish',
    license=ver['license'],
    author=ver['author'],
    author_email='',
    keywords='',
    description='',
    long_description='',
    install_requires=install_requires,
    python_requires='>=3.6',
    tests_require=tests_require,
    entry_points={
        'console_scripts': [
                'pfish = parrotfish.core:run'
        ],
    }
)

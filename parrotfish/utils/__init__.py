"""
General utilities
"""

import json
from os import sep

import inflection

from .diff import compare_content
from .log import CustomLogging

def sanitize_filename(name):
    return name.replace(sep, '_')


def sanitize_attribute(name):
    return sanitize_filename(name).replace(' ', '_')


def format_json(j):
    return json.dumps(j, indent=4, sort_keys=True)


def attributerize(word):
    return inflection.parameterize(word).replace('-', '_')


def get_callables(obj):
    return [key for key, val in obj.__dict__.items() if callable(val)
            and not key.startswith("_")]
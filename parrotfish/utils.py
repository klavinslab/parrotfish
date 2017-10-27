from os import sep
import json

def sanitize_filename(name):
    return name.replace(sep, '_')

def format_json(j):
    return json.dumps(j, indent=4, sort_keys=True)
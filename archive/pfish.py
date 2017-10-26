import difflib
import sys
from datetime import datetime
from random import randint

from pydent import *

from archive.shell_colors import Colors as c

# Make sure we have a place to save protocols
REPOS_PATH = "./repos.json"
META_DIR = "./meta"
if not os.path.exists(META_DIR):
    os.makedirs(META_DIR)

def load_json(file_path):
    try:
        with open(file_path, 'r') as json_file:
            return json.loads(json_file.read())
    except (FileNotFoundError, ValueError) as e:
        print(e)
        print("Creating JSON file...")
        with open(file_path, 'w') as json_file:
            json_file.write(json.dumps({}))
        return {}

def write_json(file_path, dictionary):
    try:
        with open(file_path, 'w') as json_file:
            json_file.write(json.dumps(dictionary, indent=4, separators=(',', ': ')))
    except FileNotFoundError:
        raise

def load_repos(directory):
    repos = load_json(REPOS_PATH)
    if directory not in repos:
        repos[directory] = {
            "meta_name": randint(0, sys.maxsize)
        }
        write_json(REPOS_PATH, repos)

    return repos

def load_metadata(directory):
    # Find metadata JSON file
    repos = load_repos(directory)

    # Load metadata
    meta_path = "{0}/{1}.json".format(META_DIR, repos[directory]["meta_name"])
    return load_json(meta_path)

def write_metadata(directory, dictionary):
    repos = load_json(REPOS_PATH)
    meta_path = "{0}/{1}.json".format(META_DIR, repos[directory]["meta_name"])
    write_json(meta_path, dictionary)

def to_epoch(date_string):
    if date_string[-3] == ":":
        date_string = date_string[:-3]+date_string[-2:]
    date = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S%z')
    epoch = int(date.strftime('%s'))

    return epoch

# Set remote server for directory
def set_remote(directory, url, username, password):
    repos = load_repos(directory)

    repos[directory]["remote"] = {
        "url": url,
        "username": username,
        "password": password
    }

    write_json(REPOS_PATH, repos)
    use_remote(directory)
    print("Remote server set for this directory")

def use_remote(directory):
    repos = load_repos(directory)

    try:
        remote_info = repos[directory]["remote"]
        config = {
            "aquarium_url": remote_info["url"],
            "login": remote_info["username"],
            "password": remote_info["password"]
        }

        with open("./trident/py/config.py", "w") as config_file:
            config_file.write("config = {0}".format(config))

        return True
    except:
        print("Could not run pfish command. Have you associated this directory with a remote server yet with 'pfish set_remote'?")

        return False

# Save remote code to DIR
def pull(directory):
    if not use_remote(directory): return

    meta = load_metadata(directory)

    aq.login()
    for ot in aq.OperationType.all():
        code = ot.code("protocol")
        if ot.name.find('/') != -1 or code is None:
            print("SKIPPED -- {0}".format(ot.name))
            continue

        # Make file path
        folder_name = "{0}/{1}".format(directory, ot.category)
        file_path = "{0}/{1}.rb".format(folder_name, ot.name)

        if file_path not in meta or meta[file_path]["remote_last_updated"] < to_epoch(code.updated_at):
            # -- PULL --
            # Create folder
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)

            # Write file
            with open(file_path, 'w') as file:
                file.write(code.content)

            # Update meta
            meta[file_path] = {
                "name": ot.name,
                "category": ot.category,
                "remote_last_updated": to_epoch(code.updated_at),
                "local_last_updated": os.path.getmtime(file_path)
            }
            print('UPDATED -- {0}'.format(file_path))

    write_metadata(directory, meta)

# Push local code to remote
def push(directory):
    if not use_remote(directory): return

    meta = load_metadata(directory)

    aq.login()
    file_conflict = False
    for file_path in meta:
        if meta[file_path]["local_last_updated"] < os.path.getmtime(file_path):
            # Find OperationType
            category = meta[file_path]["category"]
            name = meta[file_path]["name"]
            ots = aq.OperationType.where({"category": category, "name": name})
            if ots is None or len(ots) == 0:
                print("Could not find protocol {0}".format(name))
            else:
                ot = ots[0]
                # Check if we have latest version
                code = ot.code("protocol")
                if meta[file_path]["remote_last_updated"] == to_epoch(code.updated_at):
                    # -- PUSH --
                    # Push code
                    with open(file_path, 'r') as file:
                        code.content = file.read()
                        code.update()

                    # Update meta
                    meta[file_path]["remote_last_updated"] = to_epoch(code.updated_at)
                    meta[file_path]["local_last_updated"] = os.path.getmtime(file_path)

                    print('PUSHED -- {0}'.format(file_path))
                else:
                    # Show diff
                    with open(file_path, 'r') as file:
                        form_file = [line[0:-1] for line in file.readlines()]
                        form_code = code.content.split('\n')[0:-1]
                        diff = difflib.ndiff(form_code, form_file)

                        diff = [c.RED + line + c.NC if line[0] == '-' else line for line in diff]
                        diff = [c.GREEN + line + c.NC if line[0] == '+' else line for line in diff]

                        print("\n{white}Diff for {path}{nc}".format(path = file_path, white = c.BWHITE, nc = c.NC))
                        print('\n'.join(list(diff)))

                        file_conflict = True

    if file_conflict:
        print("\n{white}WARNING: At least one protocol has been edited since you last pulled{nc}".format(white = c.BWHITE, nc = c.NC))
        print("{gray}Please pull the most recent code version before you push your changes{nc}".format(gray = c.GRAY, nc = c.NC))
    else:
        print("{white}Push successfully completed!{nc}".format(white = c.BWHITE, nc = c.NC))

    write_metadata(directory, meta)

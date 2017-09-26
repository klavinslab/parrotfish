import sys, os, json
from time import gmtime, strftime
from datetime import datetime
import difflib

# Get that pydent
sys.path.append('./trident/py')
import aq

# Make sure we have a place to save protocols
DIR = "./protocols"
META_DIR = './meta.json'
if not os.path.exists(DIR):
    os.makedirs(DIR)

def load_metadata():
    try:
        with open(META_DIR, 'r') as meta:
            return json.loads(meta.read())
    except FileNotFoundError:
        with open(META_DIR, 'w') as meta:
            meta.write(json.dumps({}))
        return {}

def write_metadata(meta):
    try:
        with open(META_DIR, 'w') as meta_file:
            meta_file.write(json.dumps(meta, indent=4, separators=(',', ': ')))
    except FileNotFoundError:
        raise

def to_epoch(date_string):
    if date_string[-3] == ":":
        date_string = date_string[:-3]+date_string[-2:]
    date = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S%z')
    epoch = int(date.strftime('%s'))

    return epoch

# Save remote code to DIR
def pull():
    meta = load_metadata()

    aq.login()
    for ot in aq.OperationType.all():
        code = ot.code("protocol")
        if ot.name.find('/') != -1 or code is None:
            print("SKIPPED -- {0}".format(ot.name))
            continue

        # Make file path
        folder_name = './protocols/' + ot.category
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

    write_metadata(meta)

# Push local code to remote
def push():
    meta = load_metadata()

    aq.login()
    for file_path in meta:
        if meta[file_path]["local_last_updated"] < os.path.getmtime(file_path):
            # Find OperationType
            category = meta[file_path]["category"]
            name = meta[file_path]["name"]
            ot = aq.OperationType.where({"category": category, "name": name})[0]
            
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

                    diff = ["\033[1;31m" + line + "\033[0m" if line[0] == '-' else line for line in diff]
                    diff = ["\033[1;32m" + line + "\033[0m" if line[0] == '+' else line for line in diff]

                    print("\033[1;37mDiff for {0}\033[0m".format(file_path))
                    print("\033[0;37m  - You must pull the most recent code version in order to push your changes\033[0m\n")
                    print('\n'.join(list(diff)))

    write_metadata(meta)

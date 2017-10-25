[![travis build](https://img.shields.io/travis/klavinslab/parrotfish.svg)](https://travis-ci.org/klavinslab/parrotfish)
[![Coverage Status](https://coveralls.io/repos/github/klavinslab/parrotfish/badge.svg?branch=master)](https://coveralls.io/github/klavinslab/parrotfish?branch=master)
[![PyPI version](https://badge.fury.io/py/REPO.svg)](https://badge.fury.io/py/REPO)

![module_icon](images/module_icon.png?raw=true)

#### Build/Coverage Status
Branch | Build | Coverage
:---: | :---: | :---:
**master** | [![travis build](https://img.shields.io/travis/klavinslab/parrotfish/master.svg)](https://travis-ci.org/klavinslab/parrotfish/master) | [![Coverage Status](https://coveralls.io/repos/github/klavinslab/parrotfish/badge.svg?branch=master)](https://coveralls.io/github/klavinslab/parrotfish?branch=master)
**development** | [![travis build](https://img.shields.io/travis/klavinslab/parrotfish/development.svg)](https://travis-ci.org/klavinslab/parrotfish/development) | [![Coverage Status](https://coveralls.io/repos/github/klavinslab/parrotfish/badge.svg?branch=development)](https://coveralls.io/github/klavinslab/parrotfish?branch=development)

# **parrotfish**

Code and manage your Aquarium protocols and libraries through your IDE

# Version/Status

Code and ideas were taken from Garrett Newman. This branch is rebranding the interface
and packaging to be more convenient for other users to adopt.

Note that this version requires the new version of Trident that utilizes Pillowtalk.

# Installation
```
pip install parrotfish
```

# Usage

There are two ways to use parrotfish. The first is by the command line interface, which
allows you to build up bash-like scripts for development. The second is through a python interpreter.

## Command Line Interface (CLI)

Using parrotfish through the CLI is easy. The following commands are exposed through the
CLI: `register`, `pull`, `checkout`, `push`, `fetch`, `set_category`, `reset``.

### help

To list the available commands, type:
```bash
python parrotfish.py --help
```
```
>>> Available Commands:

        - checkout
        - clear
        - fetch
        - push
        - register
        - reset
        - set_category
```

To get help with any particular command, type something like:
```bash
python parrotfish.py register -h
```
which will display a information of the arguments

#### CLI usage

A typical parrotfish session may look like:

```bash
# register a new sessions
python parrotfish.py register jjohn mypassword 165.13.2.2131 nursery

# set the OperationType category
python parrotfish.py set_category mycategory

# checkout nursery session
python parrotfish.py checkout nursery

# fetch code from nursery server
python parrotfish.py fetch
```

##### Registration

When you call `register user pass usr session_name`, parrotfish will create a new folder in
 the bin/protocols/session_name. Fetching protocols will pull protocols from Aquarium to that folder while
 you are still checkingout that session.

Registration will also save the session states in a pickle file located in the bin folder. This means that
after registration *it is unnecessary to re-register your session.* Parrotfish will automatically reload your last
session. This is a necessary feature in order to be able to chain CLI commands together into a meaningful script.

To remove files or sessions, you can use the `clear` or `reset` command. You can clear a particular category of
protocols from your local machine. Note the optional `force=True` argument. When this is not present, parrotfish will
prompt you to confirm the deletion of the protocols.

```bash
python parrotfish.py checkout mysession
python parrotfish.py set_category mycategory
python parrotfish.py clear force=True
```

To remove *all files and sessions*, you use the `reset` command, which will remove the pickled session_state file
and **all** protocols in **all** categories.
```bash
python parrotfish.py reset force=True
```

##### Switching sessions

You can switch sessions using the `checkout` command:

```bash
python parrotfish.py checkout production

# do production server stuff here
```

You can change the category your checking out using the `set_category` command.
```bash
python parrotfish.py set_category mycategory
```

##### fetch
coming soon...

##### push
coming soon...

##### push
coming soon...

##### pull
coming soon...

### Python usage

Python commands directly mirror the CLI commands. All methods
return the ParrotFish class and so can be chained together easily into one-liners
```python
from parrotfish import *

# load from previous registration
ParrotFish.load()
ParrotFish.checkout("nursery").set_category("cloning").fetch()

# or using the checkout shortcut
ParrotFish.nursery.set_category("cloning").fetch()
```
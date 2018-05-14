[![travis build](https://img.shields.io/travis/klavinslab/parrotfish.svg)](https://travis-ci.org/klavinslab/parrotfish)
[![Coverage Status](https://coveralls.io/repos/github/klavinslab/parrotfish/badge.svg?branch=master)](https://coveralls.io/github/klavinslab/parrotfish?branch=master)
[![PyPI version](https://badge.fury.io/py/REPO.svg)](https://badge.fury.io/py/REPO)

![module_icon](images/module_icon.png?raw=true)

#### Build/Coverage Status

|     Branch      |                                                                      Build                                                                      |                                                                                     Coverage                                                                                     |
| :-------------: | :---------------------------------------------------------------------------------------------------------------------------------------------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
|   **master**    |      [![travis build](https://img.shields.io/travis/klavinslab/parrotfish/master.svg)](https://travis-ci.org/klavinslab/parrotfish/master)      |      [![Coverage Status](https://coveralls.io/repos/github/klavinslab/parrotfish/badge.svg?branch=master)](https://coveralls.io/github/klavinslab/parrotfish?branch=master)      |
| **development** | [![travis build](https://img.shields.io/travis/klavinslab/parrotfish/development.svg)](https://travis-ci.org/klavinslab/parrotfish/development) | [![Coverage Status](https://coveralls.io/repos/github/klavinslab/parrotfish/badge.svg?branch=development)](https://coveralls.io/github/klavinslab/parrotfish?branch=development) |

# **parrotfish**

Code and manage your Aquarium protocols and libraries through your IDE

## Version/Status

Code and ideas were taken from Garrett Newman. This branch is rebranding the interface
and packaging to be more convenient for other users to adopt.

Note that this version requires the new version of Trident that utilizes Pillowtalk.

## Installation

### Requirements

* install this version of [trident](https://github.com/klavinslab/trident/tree/feature-pillowtalk-apiwrapper)
  * cd to trident directory
  * run `pip install .`

```
cd to/directory/parrotfish
pip install parrotfish
```

## Usage

Once installed, the command line interface is automatically exposed. Take a look at the available
commands by typing

```bash
pfish
```

### Logging in

```bash
pfish register <username> <password> <aquarium_url> <session_name>
```

### Managing environment

List current environment state by:

```bash
pfish state
```

Set your session by name:

```bash
pfish set_session <session_name>
```

Set your current category ("all" for all categories):

```bash
pfish set_category <category_name>
```

List available categories on the server:

```bash
pfish categories
```

### Managing code

Listing repo location:

```bash
pfish repo
```

Moving your repo:

```bash
pfish move_repo <path_to_new_location>
```

Get code for current session and category:

```bash
pfish fetch
```

Push code for current session and category:

```bash
pfish push
```

### Testing Operation Types

Please consult the [Operation Type Testing documentation](./docs/operation_type_testing.md) for instructions on how to test Operation Types with Parrotfish.

## Setting up scripts

A fetch script may look like

```bash
#!/usr/bin/env bash

pfish set_session nursery
pfish set_category Cloning
pfish fetch
```

A push script may look like:

```bash
#!/usr/bin/env bash

pfish set_session nursery
pfish set_category Cloning
pfish push
```

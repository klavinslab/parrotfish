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

Code and manage your Aquarium protocols and libraries through your IDE. **ParrotFish** (aka **pfish**)
is a cli interface for downloading ('fetch') and uploading ('push') Aquarium protocols.

### Features:

* fetch operation_type definitions, protocol code, documentation, precondition, and cost model to you local machine
* push changes to protocol, documentation, precondition, and cost models **all** at once

## Getting Started

Install pfish using pip3. Download parrotfish and cd into the directory. Install by running the following:

```
pip3 install .
```

Once installed, a command line interface is provided in your terminal by running:

```
pfish
```

Try it to checkout the CLI documentation and help docs.

To actually begin using pfish, your must register an Aquarium session to your computer. To do this,
run the following in your terminal replacing your login credentials with your Aquarium login.

```bash
pfish register <username> <password> <aquarium_url> <session_name>
```

The session_name will be the string you use to reference this session. To see the list of your registered sessions,
run

```bash
pfish sessions
```

Which should return something like:

```
nursery:        <AqSession(name=nursery, AqHTTP=<AqHTTP(vrana, http://52.27.43.242:81/)>))>
production:     <AqSession(name=production, AqHTTP=<AqHTTP(vrana, http://52.27.43.242/)>))>
```

Pfish maintains a memory of which session you are currently working in. To see which session you are currently
working in run. You may set the session by running:

```bash
pfish set-session <session_name>
```

replacing <session_name> with the actual name of your session.

Finally, pfish needs somewhere to save the your protocols. To set the repo location (or move existing protocols), run:

```bash
pfish move-repo <path>
```.

### Running in *Shell* mode

Pfish also features an interactive shell to help get you started. The shell offers suggestions and autocomplete
to help you run pfish commands. For example, the following video demonstrates switching sessions, fetching a protocol
category, and listing the protocols in you local repo:

![shell](/docsrc/pfish_shell.gif)

Begin the shell by running:

```
pfish shell
```

Click the **Tab** button to view a list of command and argument available in pfish. You may exit the shell by entering
`exit`.

## Version/Status

This is currently in development. To move to production, likely the following features and fixes would need to be added:

* better tests
* CI tests on windows, mac, and linux?
* docker integration
* removal of encryption features that will likely confuse users down the road

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
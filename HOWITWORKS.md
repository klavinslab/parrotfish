# How Parrotfish works

*doc author: Justin Vrana*

Parrotfish uses a Session-flavored Trident version. As of 2017-10-26, sessions have yet to be incorporated into the main
branch of Trident.

#### Features
* managing multiple connections to Aquarium including
    *   different logins
    *   different servers
    *   custom session names
* exposure to command line *and* internal python scripts
    * `fetch` - get protocols from server
    * `push` - push protocol code from local machine to server
    * `pull` - pull code from one session to another session (e.g. nursery to production)
    * `reset` - resets sessions and local machine protocols
    * `clear` - clear local session files
    * `set_remote` - move or set local protocol folder
    * `checkout` - use named session
    * `register` - make a new session with an Aquarium server
    * `set_verbose` - verbose log messages
* helpful documentation by running `python pfish.py --help` or `python pfish.py cmd -h`
* automatic saving and loading of previous sessions and session states
* ability to move your protocol directories
* isolated testing environment for unittests
* packaging into setup.py for easy installation

#### Future features?
* creating new OperationTypes, FieldTypes, Libraries, etc. through your IDE (Ben's idea)


## Environments

An environment captures the following:
- Aquarium sessions (i.e. logins to various servers)
- the location of the bin of protocols on your local machine

You can set your session to and existing or new session by running the `set_env` command
```python
ParrotFish.set_env("testing_env.pkl")
```

Setting an environment allows you to manage your sessions and protocols in isolation. By default, a 'default_env.pkl'
environment will be created for you. There should be no reason to create a new environment unless you are running tests
or want to simultaneously manage more than one set of sessions for some reason. Unittesting, for example, happens by using
an isolated testing environment with a bin located in the parrotfish/tests folder without affecting other environments
or bins.

**Note:** currently you cannot run set_env from the command line as it always defaults to your default environment. I did not
see any use case for setting environments other than internal testing. This feature can be added upon request.

## Sessions

With your environment set (or default environment given to you), your Aquarium sessions are automatically loaded along
with the expected location of your protocol bin directory. Now any parrotfish commands will act upon those sessions and
protocols located only in the environments' bin.

A user may have multiple Aquarium sessions and servers they are connected to. A session captures an individual connection
to an Aquarium server (login, password, aquarium_url) and has a name (session_name). Each session will have its own directory
which contains protocol code grouped by category.

You can register a session by running the `register` command. You can set your current session to an existing session by
 running the `set_session` command. Once set, all commands will modify code located in that session's directory.

Session information is stored in the `.environ/default_env.pkl` file and is loaded anytime a command line command is run.

### File structure

`.environ/default_env.pkl` - saves everything about the session state so that you don't have to re-login everytime. This
file should never be moved and is expected to be in `parrotfish/.sessions/state.pkl`, where parrotfish is installed.
The all important `state.pkl` file contains information on your last login, all of your sessions, and the expected location of your bin
folder. Don't worry, if this file gets deleted, a new one will be automatically created. You can force remove by running
the `reset` command.

`path/to/parrofish/bin` - Folder in which stores all code. This directory can be *anywhere* on your local machine and
can be moved using the `set_remote` command.

`bin/protocols` - Folder for all your sessions. Each session should have a directory. You can delete all of your code and files
by running the `reset` command (directories will be automatically generated when you need it).

`bin/protocols/<session_name>` - Folder containing session-specific code. Within the session directory,
 each protocol category will also have its own directory.

`bin/protocols/<session_name>/<category>` - Protocol code for the given session and protocol category.

`bin/protocols/<session_name>/code.pkl` - Save OperationTypes and Libraries for last fetch

Locations of bin folders can be updated by `set_remote` command, which copies the contents of the
current folder to a new location. Any parrotfish commands now operate on the new bin folder.
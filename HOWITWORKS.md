# How Parrotfish works

Parrotfish uses a Pillowtalk-flavored Trident version.

Named connections to Aquarium servers are made via `register` command. The named session creates
a folder in your bin folder for that session. Protocol code is grouped by category (a directory for each)

### File structure

`./.sessions/state.pkl` - saves everything about the session state so that you don't have to re-login everytime. This
file should never be moved and is expected to be in `parrotfish/.sessions/state.pkl`, where parrotfish is installed.
The all important `state.pkl` file contains information on your last login, all of your sessions, and the expected location of your bin
folder. Don't worry, if this file gets deleted, a new one will be automatically created. You can force remove by running
the `reset` command.

`path/to/parrofish/bin` - Folder in which stores all code. This directory can be anywhere on your local machine and
can be moved using the `set_remote` command.

`bin/protocols` - Folder for all your sessions. Each session should have a directory. You can delete all of your code and files
by running the `reset` command (directories will be automatically generated when you need it).

`bin/protocols/session_name` - Folder containing session-specific code. Each protocol category will have its own directory.

`bin/protocols/session_name/code.pkl` - Save OperationTypes and Libraries for last fetch

Locations of bin folders can be updated by `set_remote` command, which copies the contents of the
current folder to a new location. Any parrotfish commands now operate on the new bin folder.
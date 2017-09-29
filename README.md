# PARROTFISH

Have you ever wanted to write a protocol? If so, parrotfish is for you!

## Prerequisites
- [Python3](https://www.python.org/downloads/)

## Installation
1. Clone the Parrotfish repository with
```bash
git clone https://github.com/klavinslab/parrotfish
```
2. Set up your Parrotfish directory with
```bash
bash setup.sh
```
3. Navigate to parrotfish/bin, and [install and configure Trident](https://github.com/klavinslab/trident) there.

## Using Parrotfish
### pfish set_remote [url] [username] [password]
This associates a remote Aquarium server with the current directory (a prerequisite for `push` and `pull`).
### pfish pull
This clones all Operation Type code from the specified server via Trident into the current directory.
### pfish push
This pushes all Parrotfish-tracked code in the current directory to the specified server via Trident, except when a given file to be pushed has been updated on the server since the last pull.

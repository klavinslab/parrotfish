#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ "$1" = "push" ] || [ "$1" = "pull" ] ; then
    DIR=$PWD
    (cd $SCRIPT_DIR && python3 -c 'from pfish import *; '$1'('\"$DIR\"')')
else
    echo "Expecting a valid pfish command (add_remote, push, or pull)"
fi

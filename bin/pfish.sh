#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ "$1" = "push" ] || [ "$1" = "pull" ] ; then
    DIR=$PWD
    (cd $SCRIPT_DIR && python3 -c 'from pfish import *; '$1'('\"$DIR\"')')
elif [ "$1" = "set_remote" ] ; then
    if [ "$#" -ne 4 ] ; then
        echo "Expecting three arguments for set_remote: pfish set_remote [url] [username] [password]"
    else
        DIR=$PWD
        (cd $SCRIPT_DIR && python3 -c 'from pfish import *; '$1'('\"$DIR\"','\"$2\"','\"$3\"','\"$4\"')')
    fi
else
    echo "Expecting a valid pfish command (set_remote, push, or pull)"
fi

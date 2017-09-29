#!/bin/bash

# Add pfish command
echo "alias pfish='. pfish.sh'" >> ~/.bashrc
echo "export PATH=\$PATH:"$PWD/bin >> ~/.bashrc
source ~/.bashrc

echo "Parrotfish set up and ready to go!"

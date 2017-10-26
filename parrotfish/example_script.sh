#!/usr/bin/env bash

pf=pfish_manager.py

# create some .sessions
python $pf register vrana Mountain5 http://52.27.43.242 production
python $pf register vrana Mountain5 http://52.27.43.242:81 nursery

# set category
python $pf set_category Justin

# get protocols from nursery
python $pf checkout nursery
python $pf fetch

# get protocols from production
python $pf checkout production
python $pf fetch

# push changes to nursery
python $pf checkout nursery
python $pf push

# puch changes to production
python $pf checkout production
python $pf push

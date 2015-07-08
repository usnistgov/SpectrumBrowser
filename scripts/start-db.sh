#!/bin/bash
CFG=$HOME/.msod/MSODConfig.json
DB_DATA_DIR=$(
    python -c 'import json; print json.load(open("'$CFG'"))["DB_DATA_DIR"]'
)
mkdir -p $DB_DATA_DIR
mongod -dbpath $DB_DATA_DIR&
pid=$!
disown $pid
echo $pid > .mongod.pid

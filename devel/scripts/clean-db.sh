#!/bin/sh
CFG=$HOME/.msod/MSODConfig.json
if [ -f $FILE  ]; then
    echo "Using file $CFG"
else
    print "$CFG not found"
    exit -1
fi
DB_DATA_DIR=$(
    python -c 'import json; print json.load(open("'$CFG'"))["DB_DATA_DIR"]'
)
if [ -z "$SB_HOME"  ]; then
    echo "$SB_HOME is empty"
    exit -1
fi
rm -rf $DB_DATA_DIR/*

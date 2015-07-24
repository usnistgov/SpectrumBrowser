#!/bin/sh
CFG=$HOME/.msod/MSODConfig.json
if [ -f $FILE  ]; then
    echo "Using file $CFG"
else
    print "$CFG not found"
    exit
fi
DB_DATA_DIR=$(
    python -c 'import json; print json.load(open("'$CFG'"))["DB_DATA_DIR"]'
)
if [ -z "$DB_DATA_DIR"  ]; then
    echo "$DB_DATA_DIR is empty"
    exit
fi
rm -rf $DB_DATA_DIR/*

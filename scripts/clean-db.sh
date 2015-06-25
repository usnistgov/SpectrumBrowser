#!/bin/sh
CFG=$HOME/.msod/MSODConfig.json
DB_DATA_DIR=$(
    python -c 'import json; print json.load(open("'$CFG'"))["DB_DATA_DIR"]'
)
rm -rf $DB_DATA_DIR/*

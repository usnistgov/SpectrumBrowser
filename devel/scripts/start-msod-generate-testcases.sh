#!/bin/bash
export MSOD_DISABLE_SESSION_ID_CHECK="True"
export MSOD_GENERATE_TEST_CASE="True"
export MSOD_UNIT_TEST_FILE=$1
if [ -n "$1" ]
then
  echo "generating test script " $1
else  
  echo "Please specify file for test script"
  exit 1
fi
source start-msod.sh

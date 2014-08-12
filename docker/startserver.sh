#!/bin/sh
#
# Start and monitor server processes

touch /var/log/flaskr

mongod --fork --logpath=/var/log/mongodb/mongod.log

python flaskr.py >> /var/log/flaskr 2>&1 &

tail -F /var/log/mongodb/mongod.log -F /var/log/flaskr

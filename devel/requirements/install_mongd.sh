#!/bin/sh
echo
echo "============== Installing mongd =============="
mkdir -p /opt/mongodb-download
mkdir -p /opt/mongodb
wget https://www.mongodb.org/dr/fastdl.mongodb.org/linux/mongodb-linux-x86_64-2.6.10.tgz/download -O /opt/mongodb-download/download
tar -xvzf /opt/mongodb-download/download -C /opt/

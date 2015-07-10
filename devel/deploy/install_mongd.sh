echo
echo "============== Installing mongd =============="
wget https://www.mongodb.org/dr/fastdl.mongodb.org/linux/mongodb-linux-x86_64-2.6.10.tgz/download -O /opt/mongodb-download/download
mkdir -p /opt/mongodb
tar -xvzf /opt/mongodb-download/download -C /opt/

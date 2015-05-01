#!/bin/bash
# Written by: Julie Kub
# Written on: 5/1/15
if [ "$1" == "-h" ]; then
    echo "Usage: sudo `basename $0` /path/to/software_file path/to/pip_file yum|apt-get"
    exit 0
fi
if [ "$#" -ne 3 ]; then
    echo "You need 3 inputs"
    echo "Usage: sudo `basename $0` /path/to/software_file path/to/pip_file yum|apt-get"
    exit 0
fi
# sudo apt-get update  # To get the latest package lists
# $1 = the file with ubuntu software to install
while read p; do
    # we may need to do an if/else for yum, e.g. "if yum list installed $p"
    # Also, command -v does not work for everything, e.g. not python-pip
    if command -v $p >/dev/null
    then
        echo $p "is already installed"
    else 
        $3 -y install $p
    fi
done <$1
# We need to install a particular version of GWT, so we need the following:
if ls /opt | grep gwt >/dev/null
then
    echo "gwt is already installed"
else
    wget -P /tmp http://storage.googleapis.com/gwt-releases/gwt-2.6.1.zip
    unzip /tmp/gwt-2.6.1 -d /opt
    echo "GWT_HOME=/opt/gwt-2.6.1" >> /etc/profile
    echo "export GWT_HOME" >> /etc/profile
    # reload /etc/profile, you can also use 'source /etc/profile':
    . /etc/profile
fi
if command -v pip
then
   echo "pip is already installed"
else
    #JEK: I was unable to get apt-get install python-pip to work,
    # The following website suggested the following:
    #  http://stackoverflow.com/questions/28917534/pip-broken-on-ubuntu-14-4-after-package-upgrade
    wget https://bootstrap.pypa.io/get-pip.py
    python get-pip.py 
fi
# $2 = the file with ubuntu python requirements.txt items to install
# JEK: I do not think we need the following, the second line seems to work:
# pip install -r $2 --no-index --find-links file:///tmp/packages
pip install -r $2


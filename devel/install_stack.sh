#!/bin/bash

# Written by: Julie Kub
# Written on: 5/1/15

script_name=${0##*/}

# If script is passed parameters (such as --help) or is not run with root
# privileges, print help and exit
if [[ -n $1 ]] || (( ${EUID} != 0 )); then
    echo "Usage: sudo ${0}" >>/dev/stderr
    exit 1
fi

# We can handle the install script being run from anywhere within the
# SpectrumBrowser directory structure by asking git for the top level of the
# current git repository... but make sure we're at least in the correct
# repository
repo_root=$(git rev-parse --show-toplevel)
if [[ ! -d ${repo_root} ]] || [[ $(basename ${repo_root}) != "SpectrumBrowser" ]]; then
    echo "${script_name}: must run from within the SpectrumBrowser git repository" >>/dev/stderr    
    exit 1
fi    


echo "=========== Detecting linux distribution  ==========="

# Detect whether script is being run from a Debian or Redhat-based system
if [[ -f /etc/debian_version ]] && pkg_manager=$(type -P apt-get); then
    echo "Detected Debian-based distribution"
    stack_requirements=${repo_root}/devel/ubuntu_stack.txt
elif [[ -f /etc/redhat-release ]] && pkg_manager=$(type -P yum); then
    echo "Detected Redhat-based distribution"
    stack_requirements=${repo_root}/devel/redhat_stack.txt
else
    echo "${script_name}: your distribution is not supported" >>/dev/stderr    
    exit 1
fi    

# Double check the file we chose exists
if [[ ! -f ${stack_requirements} ]]; then
    echo "${script_name}: ${stack_requirements} not found" >>/dev/stderr
    exit 1
fi


echo
echo "============ Installing non-python stack ============"

# Install stack
${pkg_manager} -y install $(< ${stack_requirements}) || exit 1


echo
echo "================== Installing GWT  =================="

did_set_gwt_home=0
set_gwt_home () {
    if [[ -z $1 ]]; then
        echo "set_gwt_home missing parameter" >>/dev/stderr
        exit 1
    fi

    if [[ -f /etc/profile.d/gwt_home.sh ]]; then
        echo "gwt_home.sh found in /etc/profile.d/ but GWT_HOME not in env"
        echo "Log out and back in and ensure GWT_HOME is set"
        echo "Alternately, source /etc/profile.d/gwt_home.sh && sudo -E ${0}"
        exit 1
    fi
        
    did_set_gwt_home=1
    
    echo
    echo "======= Setting GWT_HOME environment variable ======="
    echo "Found gwt-2.6.1 at $1"
    echo "# Created by ${repo_root}/devel/${script_name}" >> /etc/profile.d/gwt_home.sh
    echo "export GWT_HOME=$1" >> /etc/profile.d/gwt_home.sh

    return 0
}

if [[ -d ${GWT_HOME} ]] && [[ $(basename ${GWT_HOME}) == "gwt-2.6.1" ]]; then
    # Best case: GWT_HOME is set and points to version 2.6.1
    echo "Found gwt-2.6.1 at ${GWT_HOME}"
elif GWT_HOME=$(find /opt -type d -name 'gwt-2.6.1') && [[ -d ${GWT_HOME} ]]; then
    # Next best case: we find 2.6.1 and set GWT_HOME to it
    echo "Found gwt-2.6.1 at ${GWT_HOME}"
    set_gwt_home ${GWT_HOME}
else
    # Worst case: install
    wget -P /tmp http://storage.googleapis.com/gwt-releases/gwt-2.6.1.zip
    unzip /tmp/gwt-2.6.1 -d /opt
    rm -f /tmp/gwt-2.6.1.zip
    set_gwt_home /opt/gwt-2.6.1
fi


echo
echo "============== Installing python stack =============="

# Get pip if we don't already have it
if ! type -P pip >/dev/null; then
    echo "pip not found, installing... " >>/dev/stderr
    python ${repo_root}/devel/get-pip.py
fi

pip install --upgrade pip
pip install -r ${repo_root}/devel/python_pip_requirements.txt || exit 1

wget https://www.mongodb.org/dr/fastdl.mongodb.org/linux/mongodb-linux-x86_64-2.6.10.tgz/download -P /opt/mongodb-download
tar -xvzf /opt/mongodb/mongodb-download/download -C /opt/mongodb



echo
echo "=============== Installation complete ==============="


if (( $did_set_gwt_home )); then
    echo
    echo "You must 'source /etc/profile.d/gwt_home.sh' or log out and back in before continuing"
fi

#!/bin/bash

# Written by: Julie Kub
# Written on: 5/1/15

SCRIPT_NAME=${0##*/}

# If script is passed parameters (such as --help) or is not run with root
# privileges, print help and exit with error code 1
if [[ -n $1 ]] || (( ${EUID} != 0 )); then
    echo "Usage: sudo ${0}" >>/dev/stderr
    exit 1
fi


did_set_gwt_home=0
set_gwt_home () {
    if [[ -z $1 ]]; then
        echo "set_gwt_home missing parameter" >>/dev/stderr
        exit 1
    fi

    if grep "GWT_HOME" /etc/profile >/dev/null; then
        echo "GWT_HOME found in /etc/profile but this script can't see it"
        echo "Log out and back in and ensure GWT_HOME is set"
        echo "Alternately, source /etc/profile && sudo -E ${0}"
        exit 1
    fi
        
    did_set_gwt_home=1
    
    echo
    echo "======= Setting GWT_HOME environment variable ======="
    echo "Found gwt-2.6.1 at $1"
    echo "Saving location permenently in /etc/profile"
    echo ""                >> /etc/profile
    echo "# Added by ${0}" >> /etc/profile
    echo "GWT_HOME=$1"     >> /etc/profile
    echo "export GWT_HOME" >> /etc/profile

    return 0
}


# We can handle the install script to be run from anywhere within the
# SpectrumBrowser directory structure by asking git for the top level of the
# current git repository... but make sure we're at least in the correct
# repository, or fail with exit code 1
REPO_ROOT=$(git rev-parse --show-toplevel)

if [[ ! -d ${REPO_ROOT} ]] || [[ $(basename ${REPO_ROOT}) != "SpectrumBrowser" ]]; then
    echo "${SCRIPT_NAME}: must run from within SpectrumBrowser" >>/dev/stderr    
    exit 1
fi    


echo "=========== Detecting linux distribution  ==========="

# Detect whether script is being run from a Debian or Redhat-based system
if [[ -f /etc/debian_version ]] && PKG_MANAGER=$(type -P apt-get); then
    echo "Detected Debian-based distribution"
    STACK_REQUIREMENTS=${REPO_ROOT}/devel/ubuntu_stack.txt
elif [[ -f /etc/redhat_version ]] && PKG_MANAGER=$(type -P yum); then
    echo "Detected Redhat-based distribution"
    STACK_REQUIREMENTS=${REPO_ROOT}/devel/redhat_stack.txt
else
    echo "${SCRIPT_NAME}: your distribution is not supported" >>/dev/stderr    
    exit 1
fi    

# Double check the file we chose exists
if [[ ! -f ${STACK_REQUIREMENTS} ]]; then
    echo "${SCRIPT_NAME}: ${STACK_REQUIREMENTS} not found" >>/dev/stderr
fi


echo
echo "============ Installing non-python stack ============"

# Install stack
${PKG_MANAGER} -y install $(< ${STACK_REQUIREMENTS}) || exit 1


echo
echo "================== Installing GWT  =================="

if [[ -d ${GWT_HOME} ]] && [[ $(basename ${GWT_HOME}) == "gwt-2.6.1" ]]; then
    # Best case: GWT_HOME is set and version is 2.6.1
    echo "Found gwt-2.6.1 at ${GWT_HOME}"
elif GWT_HOME=$(find /opt -type d -name 'gwt-2.6.1') && [[ -d ${GWT_HOME} ]]; then
    # Next best case, we find 2.6.1 and set GWT_HOME to it
    echo "Found gwt-2.6.1 at ${GWT_HOME}"
    set_gwt_home ${GWT_HOME}
else
    # Worst case, install
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
    python ${REPO_ROOT}/devel/get-pip.py
fi

pip install -r ${REPO_ROOT}/devel/python_pip_requirements.txt || exit 1


echo
echo "=============== Installation complete ==============="


if (( $did_set_gwt_home )); then
    echo
    echo "You must 'source /etc/profile' or log out and back in before continuing"
fi

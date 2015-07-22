#!/bin/bash

# Written by: Julie Kub
# Written on: 5/1/15

script_name=${0##*/}

# Set your path to python 2.7 here.
PYTHON=/usr/local/bin/python2.7
PIP=/usr/local/bin/pip2.7

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
#repo_root=$(git rev-parse --show-toplevel)
#if [[ ! -d ${repo_root} ]] || [[ $(basename ${repo_root}) != "SpectrumBrowser" ]]; then
#    echo "${script_name}: must run from within the SpectrumBrowser git repository" >>/dev/stderr    
#    exit 1
#fi

echo "This is for manual installation of the build tools. "
echo "Set up python 2.7 in a virtual env  before you run this script."
echo "=========== Detecting linux distribution  ==========="

# Detect whether script is being run from a Debian or Redhat-based system
if [[ -f /etc/debian_version  ]] && pkg_manager=$(type -P apt-get); then
    echo "Detected Debian-based distribution"
    stack_requirements=ubuntu_stack.txt
elif [[ -f /etc/redhat-release ]] && pkg_manager=$(type -P yum); then
    echo "Detected Redhat-based distribution"
    stack_requirements=redhat_stack.txt
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
echo "============ Installing non-'${PYTHON}' stack ============"

# Install stack
${pkg_manager} -y install $(< ${stack_requirements}) || exit 1


echo
echo "============== Installing '${PYTHON}' stack =============="

# Get pip if we don't already have it
if ! type -P /usr/local/bin/pip2.7 >/dev/null; then
    echo "pip not found ... " >>/dev/stderr
    exit 1
fi

${PIP} install --upgrade pip
${PIP} install -r python_pip_requirements.txt || exit 1


echo
echo "=============== Installation complete ==============="



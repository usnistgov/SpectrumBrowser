#! /usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
#This software was developed by employees of the National Institute of
#Standards and Technology (NIST), and others.
#This software has been contributed to the public domain.
#Pursuant to title 15 Untied States Code Section 105, works of NIST
#employees are not subject to copyright protection in the United States
#and are considered to be in the public domain.
#As a result, a formal license is not needed to use this software.
#
#This software is provided "AS IS."
#NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
#OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
#MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
#AND DATA ACCURACY.  NIST does not warrant or make any representations
#regarding the use of the software or the results thereof, including but
#not limited to the correctness, accuracy, reliability or usefulness of
#this software.

import json as js
import sys
import subprocess
import os


def parse_msod_config():
    configFile = open(os.environ.get("HOME") + "/.msod/MSODConfig.json")
    msodConfig = js.load(configFile)
    return msodConfig


def getProjectHome():  #finds the default directory of installation
    command = ['git', 'rev-parse', '--show-toplevel']
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    return out.strip()


def getSbHome():
    msodConfig = parse_msod_config()
    return str(msodConfig["SPECTRUM_BROWSER_HOME"])


def setPath():
    msodConfig = parse_msod_config()
    sbHome = str(msodConfig["SPECTRUM_BROWSER_HOME"])
    sys.path.append(sbHome + "/services/common")

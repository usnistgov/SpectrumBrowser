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


'''
Created on May 4, 2015

@author: local
'''
import traceback
import sys
import os
import json

bootstrap = None


def readBootStrap():
    global bootstrap
    f = None
    if bootstrap == None:
        homeDir = os.environ.get("HOME")
        if homeDir != None:
            configFile = homeDir + "/.msod/MSODConfig.json"
            print "Looking for local Config File : ", configFile
            if os.path.exists(configFile):
                f = open(configFile)
            elif os.path.exists("/etc/msod/MSODConfig.json"):
                print "Looking for global Config File /etc/msod/MSODConfig.json"
                f = open("/etc/msod/MSODConfig.json")
        elif os.path.exists("/etc/msod/MSODConfig.json"):
            f = open("/etc/msod/MSODConfig.json")
        if f == None:
            print "Cant find bootstrap configuration"
            sys.exit()
            os._exit(-1)
        try:
            configStr = f.read()
            bootstrap = json.loads(configStr)
        except:
            print sys.exc_info()
            traceback.print_exc()
            sys.exit()
            os._exit(-1)


def getSpectrumBrowserHome():
    global bootstrap
    readBootStrap()
    return str(bootstrap["SPECTRUM_BROWSER_HOME"])


def getDbHost():
    global bootstrap
    readBootStrap()
    return str(bootstrap['DB_PORT_27017_TCP_ADDR'])


def getFlaskLogDir():
    global bootstrap
    readBootStrap()
    return str(bootstrap['FLASK_LOG_DIR'])


def setPath():
    global bootstrap
    sys.path.append(getSpectrumBrowserHome() + "/services/common")


def setAdminPath():
    global bootstrap
    setPath()
    sys.path.append(getSpectrumBrowserHome() + "/services/admin")


def setSbPath():
    setPath()
    sys.path.append(getSpectrumBrowserHome() + "/services/spectrumbrowser")

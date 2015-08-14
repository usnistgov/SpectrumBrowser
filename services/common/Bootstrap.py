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
        if homeDir != None :
            configFile = homeDir + "/.msod/MSODConfig.json"
            print "Looking for local Config File : ", configFile
            if os.path.exists(configFile):
                f = open (configFile)
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
    return  str(bootstrap['DB_PORT_27017_TCP_ADDR'])

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

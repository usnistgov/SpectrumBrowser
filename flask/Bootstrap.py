'''
Created on May 4, 2015

@author: local
'''
import traceback
import sys
import os

bootstrap = None

def readBootStrap():
    global bootstrap
    if bootstrap == None:
        f = open("/var/tmp/MSODConfig.json")
        if f == None:
            print "Cant find bootstrap configuration in /var/tmp/Config.json"
            sys.exit()
            os._exit(-1)
        try:
            configStr = f.read()
            bootstrap = eval(configStr)
        except:
            print sys.exc_info()
            traceback.print_exc()
            sys.exit()
            os._exit(-1)
            
def getSpectrumBrowserHome():
    global bootstrap
    readBootStrap()
    return bootstrap["SPECTRUM_BROWSER_HOME"]

def getDbHost():
    global bootstrap
    readBootStrap()
    return  bootstrap['DB_PORT_27017_TCP_ADDR']
'''
Created on Jul 28, 2015

@author: mdb4
'''
import sys
import traceback
import util
from Defines import SERVICE_NAMES
import subprocess
import time
from Defines import STATUS
from Defines import OK,NOK,ERROR_MESSAGE,SERVICE_STATUS

def thisServiceStatus(service):
    try:
        if service in SERVICE_NAMES:
            output = subprocess.Popen(["/sbin/service",service,"status"],stdout=subprocess.PIPE)
            
            statusRawInit, errorStr = output.communicate()
            
            if not errorStr == None:
                util.debugPrint("Error String detected (status): " + str(errorStr))
                return {STATUS:NOK,ERROR_MESSAGE:errorStr}
            
            statusRaw = statusRawInit.split()
            util.debugPrint("statusRaw: " + str(statusRaw))
            
            if "running" in statusRaw:
                return {STATUS:OK,SERVICE_STATUS:"running"}
            elif "stopped" in statusRaw:
                return {STATUS:OK,SERVICE_STATUS:"stopped"}
            else:
                return {STATUS:OK,SERVICE_STATUS:"unknown"}
            
        else:
            util.errorPrint(service + " does not match a service")
            return {STATUS:NOK,ERROR_MESSAGE:service + " does not match a service"}

    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise

def stopThisService(service):
    try:
        if service in SERVICE_NAMES:
            if service == SERVICE_NAMES[0]:
                return False
            else:
                output = subprocess.Popen(["/sbin/service",service,"stop"],stdout=subprocess.PIPE)
                
                stopRawInit, errorStr = output.communicate()
            
                if not errorStr == None:
                    util.debugPrint("Error String detected (stop): " + str(errorStr))
                    return False
                
                util.debugPrint("output.communicate() (stop): " + str(stopRawInit))
                return True
        else:
            util.debugPrint(service + " does not match a service")
            return False
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise

def restartThisService(service):
    try:
        if service in SERVICE_NAMES:
            if service == SERVICE_NAMES[0]:
                return False
            else:
                output = subprocess.Popen(["/sbin/service",service,"stop"],stdout=subprocess.PIPE)
                time.sleep(3)
                output = subprocess.Popen(["/sbin/service",service,"start"],stdout=subprocess.PIPE)
                
                restartRawInit, errorStr = output.communicate()
            
                if not errorStr == None:
                    util.debugPrint("Error String detected (restart): " + str(errorStr))
                    return False
                
                util.debugPrint("output.communicate() (restart): " + str(restartRawInit))
                return True
        else:
            util.debugPrint(service + " does not match a service")
            return False
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise

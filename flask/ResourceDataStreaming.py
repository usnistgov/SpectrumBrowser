'''
Created on Jun 23, 2015

@author: mdb4
'''
import util
import authentication
import time
import gevent
from ResourceDataSharedState import MemCache
import traceback
from flask import Defines


APPLY_DRIFT_CORRECTION = False

memCache = None


def getResourceData(ws):
    """

    Handle resource data streaming requests from the web browser.
    
    Token is of the form <sessionID> => len(parts)==1

    """
    try :
        util.debugPrint( "ResourceDataStreamng:getResourceData")
        global memCache
        if memCache == None:
            memCache = MemCache()
        token = ws.receive()
        print "token = " , token
        #parts = token.split(":")
        if token == None : #or len(parts) < 2: 
            ws.close()
            return
        sessionId = token
        if not authentication.checkSessionId(sessionId,"user"):
            ws.close()
            return

        keys = Defines.RESOURCEKEYS
        
        for key in keys : 
            lastDataMessage = memCache.loadResourceData(key) 
            if not key in lastDataMessage :
                ws.close()
                util.debugPrint("Resource data not found for resource: " + key)
                return
            
            
        ## DATA TYPES:
        ## CPU = 0.0, Virtual Mem = 0.0, Disk = 0.0
        lastdatatime = -1
        resource = keys[0] # arbitrary choice
        memCache.setLastDataSeenTimeStamp(resource, 0) 
        drift = 0
        while True:
            secondsPerFrame = 1 
            lastdataseen = memCache.loadLastDataSeenTimeStamp(resource) 
            if resource in lastdataseen and lastdatatime != lastdataseen[resource]:
                lastdatatime = lastdataseen[resource] 
                currentTime = time.time()
                lastdatasent = currentTime
                memCache.setLastDataSeenTimeStamp(resource, lastdatasent)
                drift = drift + (currentTime - lastdatasent) - secondsPerFrame
                
                for key in keys : 
                    resourcedata = memCache.loadResourceData(key)
                    
                socketString = "" # this could be formatted as a JSON, but because the keys would have to be added into the array "keys" anyways,
                # it seems more efficient to format the input as follows:
                for key in keys : 
                    socketString = socketString + resourcedata[key] + ":" # "<CPU>:<VirtMem>:<Disk>"
                
                ws.send(socketString)
                # If we drifted, send the last reading again to fill in.
                if drift < 0:
                    drift = 0
                if drift > secondsPerFrame:
                    util.debugPrint("Drift detected")
                    ws.send(socketString)
                    drift = 0
            sleepTime = secondsPerFrame
            gevent.sleep(sleepTime)
    except:
        traceback.print_exc()
        ws.close()
        util.debugPrint("Error writing to websocket")

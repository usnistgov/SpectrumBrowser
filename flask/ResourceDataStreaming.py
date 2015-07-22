'''
Created on Jun 23, 2015

@author: mdb4
'''
import util
import authentication
#import time
import gevent
from ResourceDataSharedState import MemCache
import traceback
import Defines


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
        
        #parts = token.split(":")
        if token == None : #or len(parts) < 2: 
            ws.close()
            return
        sessionId = token
        if not authentication.checkSessionId(sessionId,"admin"):
            util.debugPrint( "ResourceDataStreamng:failed to authenticate: user != "+sessionId)
            ws.close()
            return

        keys = Defines.RESOURCEKEYS
        
        for key in keys : 
            lastResourceValue = memCache.loadResourceData(key) 
            if lastResourceValue == None :
                ws.close()
                util.debugPrint("Resource data not found for resource: " + key)
                return
            
        secondsPerFrame = 1 

        while True:
            socketString = ""
                
            for key in keys : 
                resourcedata = memCache.loadResourceData(key)
                socketString = socketString + str(resourcedata) + ":"
                    
            util.debugPrint("Sending thru WSocket: "+ socketString)
            ws.send(socketString)
            util.debugPrint("Success thru WSocket")
              
            sleepTime = secondsPerFrame
            gevent.sleep(sleepTime)
    except:
        traceback.print_exc()
        util.debugPrint("Error writing to resource websocket")
        util.logStackTrace(traceback)
        ws.close()
        

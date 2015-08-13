'''
Created on Jun 23, 2015

@author: mdb4
'''
import util
import authentication
import gevent
from ResourceDataSharedState import MemCache
import traceback
import Defines
import json

memCache = None


def getResourceData(ws):
    """

    Handle resource data streaming requests from the web browser.
    
    Token is of the form <sessionID> => len(parts)==1

    """
    try :
        util.debugPrint( "ResourceDataStreaming:getResourceData")
        global memCache
        if memCache == None:
            memCache = MemCache()
        token = ws.receive()
        
        if token == None : #or len(parts) < 2: 
            ws.close()
            return
        sessionId = token
        if not authentication.checkSessionId(sessionId,"admin"):
            ws.close()
            util.debugPrint( "ResourceDataStreamng:failed to authenticate: user != "+sessionId)
            return


        keys = Defines.RESOURCEKEYS
        resourceData = {}
        
        secondsPerFrame = 1
        while True:                
            for key in keys : 
                value = memCache.loadResourceData(key)
                resourceData[key] = float(value)
                
                    
            ws.send(json.dumps(resourceData))
              
            sleepTime = secondsPerFrame
            gevent.sleep(sleepTime)
    except:
        traceback.print_exc()
        util.debugPrint("Error writing to resource websocket")
        util.logStackTrace(traceback)
        ws.close()
        

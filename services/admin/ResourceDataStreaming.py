'''
Created on Jun 23, 2015

@author: mdb4
'''
import util
import authentication
import gevent
import traceback
import json
import MemCacheKeys
import memcache
from pymongo import MongoClient
from Bootstrap import getDbHost


def getResourceData(ws):
    """

    Handle resource data streaming requests from the web browser.

    Token is of the form <sessionID> => len(parts)==1

    """
    try :
        util.debugPrint( "ResourceDataStreaming:getResourceData")
        token = ws.receive()

        if token == None : #or len(parts) < 2:
            ws.close()
            return
        sessionId = token
        if not authentication.checkSessionId(sessionId,"admin"):
            ws.close()
            util.debugPrint( "ResourceDataStreamng:failed to authenticate: user != "+sessionId)
            return


        memCache = memcache.Client(['127.0.0.1:11211'], debug=0)
        keys = MemCacheKeys.RESOURCEKEYS
        resourceData = {}
        secondsPerFrame = 1
        while True:
            for resource in keys :
                key = str(resource).encode("UTF-8")
                value = memCache.get(key)
                if value != None:
                    resourceData[key] = float(value)
                else:
                    util.errorPrint("Unrecognized resource key " + key)
            
            client = MongoClient(getDbHost(),27017)
            collection = client.systemResources.dbResources
            diskValue = collection.find({},{'Disk':1,'_id':0})[0]['Disk']
	    key = str('Disk').encode("UTF-8")
            resourceData[key] = float(diskValue)

            ws.send(json.dumps(resourceData))
            sleepTime = secondsPerFrame
            gevent.sleep(sleepTime)
    except:
        traceback.print_exc()
        util.debugPrint("Error writing to resource websocket")
        util.logStackTrace(traceback)
        ws.close()


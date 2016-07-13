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
    try:
        util.debugPrint("ResourceDataStreaming:getResourceData")
        token = ws.receive()

        if token is None:  #or len(parts) < 2:
            ws.close()
            return
        sessionId = token
        if not authentication.checkSessionId(sessionId, "admin"):
            ws.close()
            util.debugPrint(
                "ResourceDataStreamng:failed to authenticate: user != " +
                sessionId)
            return

        memCache = memcache.Client(['127.0.0.1:11211'], debug=0)
        keys = MemCacheKeys.RESOURCEKEYS
        resourceData = {}
        secondsPerFrame = 1
        while True:
            for resource in keys:
                key = str(resource).encode("UTF-8")
                value = memCache.get(key)
                if value is not None:
                    resourceData[str(key)] = float(value)
                else:
                    util.errorPrint("Unrecognized resource key " + key)

            client = MongoClient(getDbHost(), 27017)
            collection = client.systemResources.dbResources
            dbResources = collection.find_one({})
            if dbResources is not None and dbResources["Disk"] is not None:
                resourceData["Disk"] = float(dbResources["Disk"])

            util.debugPrint("resource Data = " + str(json.dumps(resourceData,
                                                                indent=4)))

            ws.send(json.dumps(resourceData))
            sleepTime = secondsPerFrame
            gevent.sleep(sleepTime)
    except:
        traceback.print_exc()
        util.debugPrint("Error writing to resource websocket")
        util.logStackTrace(traceback)
        ws.close()

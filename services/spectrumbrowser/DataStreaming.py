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

from bson.json_util import dumps
import util
import authentication
import time
import gevent
from DataStreamSharedState import MemCache
import traceback
import SensorDb
from Defines import ENABLED
from Defines import STREAMING_SERVER_PORT

APPLY_DRIFT_CORRECTION = False

memCache = None


def getSensorData(ws):
    """

    Handle sensor data streaming requests from the web browser.

    """
    try:
        util.debugPrint("DataStreamng:getSensorData")
        global memCache
        if memCache is None:
            memCache = MemCache()
        token = ws.receive()
        print "token = ", token
        parts = token.split(":")
        if parts is None or len(parts) < 5:
            ws.close()
            return
        sessionId = parts[0]
        if not authentication.checkSessionId(sessionId, "user"):
            ws.close()
            return
        import SessionLock
        if SessionLock.findSessionByRemoteAddr(sessionId) is not None:
            ws.send(dumps({"status": "Streaming session already open"}))
            ws.close()
            return

        sensorId = parts[1]
        systemToDetect = parts[2]
        minFreq = int(parts[3])
        maxFreq = int(parts[4])
        util.debugPrint("sensorId " + sensorId)
        memCache.incrementStreamingListenerCount(sensorId)
        sensorObj = SensorDb.getSensorObj(sensorId)
        if sensorObj is None:
            ws.send(dumps({"status": "Sensor not found : " + sensorId}))

        bandName = systemToDetect + ":" + str(minFreq) + ":" + str(maxFreq)
        util.debugPrint("isStreamingEnabled = " + str(
            sensorObj.isStreamingEnabled()))
        lastDataMessage = memCache.loadLastDataMessage(sensorId, bandName)
        key = sensorId + ":" + bandName
        if not key in lastDataMessage or not sensorObj.isStreamingEnabled():
            ws.send(dumps(
                {"status":
                 "NO_DATA : Data message not found or streaming not enabled"}))
        else:
            ws.send(dumps({"status": "OK"}))
            util.debugPrint("DataStreaming lastDataMessage : " + str(
                lastDataMessage[key]))
            ws.send(str(lastDataMessage[key]))
            lastdatatime = -1
            drift = 0
            while True:
                secondsPerFrame = sensorObj.getStreamingSecondsPerFrame()
                lastdataseen = memCache.loadLastDataSeenTimeStamp(sensorId,
                                                                  bandName)
                if key in lastdataseen and lastdatatime != lastdataseen[key]:
                    lastdatatime = lastdataseen[key]
                    sensordata = memCache.loadSensorData(sensorId, bandName)
                    memCache.incrementDataConsumedCounter(sensorId, bandName)
                    currentTime = time.time()
                    lastdatasent = currentTime
                    drift = drift + (currentTime - lastdatasent
                                     ) - secondsPerFrame
                    ws.send(sensordata[key])
                    # If we drifted, send the last reading again to fill in.
                    if drift < 0:
                        drift = 0
                    if drift > secondsPerFrame:
                        if APPLY_DRIFT_CORRECTION:
                            util.debugPrint("Drift detected")
                            ws.send(sensordata[key])
                        drift = 0
                sleepTime = secondsPerFrame
                gevent.sleep(sleepTime)
    except:
        traceback.print_exc()
        ws.close()
        util.debugPrint("Error writing to websocket")
    finally:
        memCache.decrementStreamingListenerCount(sensorId)


def getSocketServerPort(sensorId):

    retval = {}
    global memCache
    if memCache is None:
        memCache = MemCache()
    sensor = SensorDb.getSensorObj(sensorId)
    print "sensorStatus ", sensor.getSensorStatus()
    if sensor is None or sensor.getSensorStatus() != ENABLED \
        or not sensor.isStreamingEnabled():
        retval["port"] = -1
        return retval
    retval["port"] = STREAMING_SERVER_PORT
    return retval

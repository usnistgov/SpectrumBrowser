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
    try :
        util.debugPrint("DataStreamng:getSensorData")
        global memCache
        if memCache == None:
            memCache = MemCache()
        token = ws.receive()
        print "token = " , token
        parts = token.split(":")
        if parts == None or len(parts) < 5:
            ws.close()
            return
        sessionId = parts[0]
        if not authentication.checkSessionId(sessionId, "user"):
            ws.close()
            return
        import SessionLock
        if SessionLock.findSessionByRemoteAddr(sessionId) != None:
            ws.send(dumps({"status":"Streaming session already open"}))
            ws.close()
            return

        sensorId = parts[1]
        systemToDetect = parts[2]
        minFreq = int(parts[3])
        maxFreq = int(parts[4])
        util.debugPrint("sensorId " + sensorId)
        memCache.incrementStreamingListenerCount(sensorId)
        sensorObj = SensorDb.getSensorObj(sensorId)
        if sensorObj == None:
            ws.send(dumps({"status": "Sensor not found : " + sensorId}))

        bandName = systemToDetect + ":" + str(minFreq) + ":" + str(maxFreq)
        util.debugPrint("isStreamingEnabled = " + str(sensorObj.isStreamingEnabled()))
        lastDataMessage = memCache.loadLastDataMessage(sensorId, bandName)
        key = sensorId + ":" + bandName
        if not key in lastDataMessage or not sensorObj.isStreamingEnabled() :
            ws.send(dumps({"status":"NO_DATA : Data message not found or streaming not enabled"}))
        else:
            ws.send(dumps({"status":"OK"}))
            ws.send(str(lastDataMessage[key]))
            lastdatatime = -1
            drift = 0
            while True:
                secondsPerFrame = sensorObj.getStreamingSecondsPerFrame()
                lastdataseen = memCache.loadLastDataSeenTimeStamp(sensorId, bandName)
                if key in lastdataseen and lastdatatime != lastdataseen[key]:
                    lastdatatime = lastdataseen[key]
                    sensordata = memCache.loadSensorData(sensorId, bandName)
                    memCache.incrementDataConsumedCounter(sensorId, bandName)
                    currentTime = time.time()
                    lastdatasent = currentTime
                    drift = drift + (currentTime - lastdatasent) - secondsPerFrame
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
    if memCache == None:
        memCache = MemCache()
    sensor = SensorDb.getSensorObj(sensorId)
    print "sensorStatus ", sensor.getSensorStatus()
    if sensor == None or sensor.getSensorStatus() != ENABLED \
        or not sensor.isStreamingEnabled():
        retval["port"] = -1
        return retval
    retval["port"] = STREAMING_SERVER_PORT
    return retval







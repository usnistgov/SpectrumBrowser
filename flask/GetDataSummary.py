import populate_db
from flask import request,make_response,jsonify,abort
import timezone
import util
import numpy as np
import time
import pymongo
import msgutils
from Defines import TIME_ZONE_KEY,SENSOR_ID,SECONDS_PER_DAY,FFT_POWER, SWEPT_FREQUENCY,FREQ_RANGE
import DbCollections
import DataMessage
import Message
import SensorDb
import SessionLock

def getDataSummary(sensorId, locationMessage):
    """
    get the summary of the data corresponding to the location message.
    """
    locationMessageId = str(locationMessage["_id"])
    # min and specifies the freq band of interest. If nothing is specified or the freq is -1,
    # then all frequency bands are queried.
    minFreq = int (request.args.get("minFreq", "-1"))
    maxFreq = int(request.args.get("maxFreq", "-1"))
    sys2detect = request.args.get("sys2detect",None)
    # Check the optional args.
    if minFreq != -1 and maxFreq != -1 and sys2detect != None:
        freqRange = msgutils.freqRange(sys2detect,minFreq, maxFreq)
    elif minFreq == -1 and (maxFreq != -1 or sys2detect != None) :
        util.debugPrint("minFreq not specified")
        abort(400)
    elif maxFreq == -1 and (minFreq != -1 or sys2detect != None):
        util.debugPrint("maxFreq not specified")
        abort(400)
    elif sys2detect != None and (minFreq != -1 or maxFreq != -1):
        util.debugPrint("sys2detect not specified")
        abort(400)
    else:
        freqRange = None
    # tmin and tmax specify the min and the max values of the time range of interest.
    tmin = request.args.get('minTime', '')
    dayCount = request.args.get('dayCount', '')
    tzId = locationMessage[TIME_ZONE_KEY]
    query = { SENSOR_ID: sensorId, "locationMessageId":locationMessageId }
    msg = DbCollections.getDataMessages(sensorId).find_one(query)
    if msg == None:
        return jsonify({"status":"NOK","ErrorMessage":"No Location Message"})
    
    measurementType = DataMessage.getMeasurementType(msg)

    if tmin == '' and dayCount == '':
        query = {SENSOR_ID: sensorId, "locationMessageId":locationMessageId }
        tmin = msgutils.getDayBoundaryTimeStamp(msg)
        if measurementType == FFT_POWER:
           dayCount = 14
        else:
           dayCount = 30
        mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin), tzId)
        maxtime = mintime + int(dayCount) * SECONDS_PER_DAY
    elif tmin != ''  and dayCount == '' :
        mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin), tzId)
        if measurementType == FFT_POWER:
           dayCount = 14
        else:
           dayCount = 30
        mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin), tzId)
        maxtime = mintime + int(dayCount) * SECONDS_PER_DAY
    else:
        mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin), tzId)
        maxtime = mintime + int(dayCount) * SECONDS_PER_DAY

    if freqRange == None:
        query = { SENSOR_ID: sensorId, "locationMessageId":locationMessageId, \
                     "t": { '$lte':maxtime, '$gte':mintime}  }
    else:
        query = { SENSOR_ID: sensorId, "locationMessageId":locationMessageId, \
                 "t": { '$lte':maxtime, '$gte':mintime}, FREQ_RANGE:freqRange }

    util.debugPrint(query)
    cur = DbCollections.getDataMessages(sensorId).find(query)
    if cur == None:
        errorStr = "No data found"
        return jsonify({"status":"NOK","ErrorMessage":"No Data Found"})
    nreadings = cur.count()
    cur.sort('t',pymongo.ASCENDING)
    if nreadings == 0:
        util.debugPrint("No data found. zero cur count.")
        del query['t']
        msg = DbCollections.getDataMessages(sensorId).find_one(query)
        if msg != None:
            tStartDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg["t"], tzId)
            if dayCount == '':
                query["t"] = {"$gte":tStartDayBoundary}
            else:
                maxtime = tStartDayBoundary + int(dayCount) * SECONDS_PER_DAY
                query["t"] = {"$gte":tStartDayBoundary, "$lte":maxtime}
            cur = DbCollections.getDataMessages(sensorId).find(query)
            nreadings = cur.count()
        else :
            return jsonify({"status":"NOK","ErrorMessage":"No Data Found"})


    util.debugPrint("retrieved " + str(nreadings))
    cur.batch_size(20)
    cur.sort("t",pymongo.ASCENDING)
    minOccupancy = 10000
    maxOccupancy = -10000
    maxFreq = 0
    minFreq = -1
    meanOccupancy = 0
    minTime = time.time() + 10000
    minLocalTime = time.time() + 10000
    maxTime = 0
    lastMessage = None
    tStartDayBoundary = 0
    tStartLocalTimeTzName = None
    for msg in cur:
        if DataMessage.getMeasurementType(msg) == FFT_POWER :
            minOccupancy = np.minimum(minOccupancy, DataMessage.getMinOccupancy(msg))
            maxOccupancy = np.maximum(maxOccupancy, DataMessage.getMaxOccupancy(msg))
        else:
            minOccupancy = np.minimum(minOccupancy, DataMessage.getOccupancy(msg))
            maxOccupancy = np.maximum(maxOccupancy, DataMessage.getOccupancy(msg))
        maxFreq = np.maximum(DataMessage.getFmax(msg), maxFreq)
        if minFreq == -1 :
            minFreq = DataMessage.getFmin(msg)
        else:
            minFreq = np.minimum(DataMessage.getFmin(msg), minFreq)
        if "meanOccupancy" in msg:
            meanOccupancy += DataMessage.getMeanOccupancy(msg)
        else:
            meanOccupancy += DataMessage.getOccupancy(msg)
        minTime = int(np.minimum(minTime, Message.getTime(msg)))
        maxTime = np.maximum(maxTime, Message.getTime(msg))
        lastMessage = msg
    (tEndReadingsLocalTime, tEndReadingsLocalTimeTzName) = timezone.getLocalTime(lastMessage['t'], tzId)
    tEndDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(lastMessage["t"], tzId)
    # now get the global min and max time of the aquistions.
    if 't' in query:
        del query['t']

    cur = DbCollections.getDataMessages(sensorId).find(query)
    acquisitionCount = cur.count()
    sortedCur = cur.sort('t',pymongo.ASCENDING)
    firstMessage = sortedCur.next()
    tAquisitionStart = firstMessage['t']
    tStartDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(tAquisitionStart, tzId)
    (minLocalTime, tStartLocalTimeTzName) = timezone.getLocalTime(msg['t'], tzId)

    cur = DbCollections.getDataMessages(sensorId).find(query)
    sortedCur = cur.sort('t', pymongo.DESCENDING)
    lastMessage = sortedCur.next()
    tAquisitionEnd = lastMessage['t']

    cur = DbCollections.getDataMessages(sensorId).find(query)
      
    acquistionMaxOccupancy = -1000
    acquistionMinOccupancy = 1000
    acquistionMeanOccupancy = 0
    if measurementType == SWEPT_FREQUENCY:
        for msg in cur :
            acquistionMaxOccupancy = np.maximum(acquistionMaxOccupancy,DataMessage.getOccupancy(msg))
            acquistionMinOccupancy = np.minimum(acquistionMinOccupancy,DataMessage.getOccupancy(msg))
            acquistionMeanOccupancy = acquistionMeanOccupancy + DataMessage.getOccupancy(msg)
    else:
        for msg in cur:
            acquistionMaxOccupancy = np.maximum(acquistionMaxOccupancy,DataMessage.getMaxOccupancy(msg))
            acquistionMinOccupancy = np.minimum(acquistionMinOccupancy,DataMessage.getMinOccupancy(msg))
            acquistionMeanOccupancy = acquistionMeanOccupancy + DataMessage.getMeanOccupancy(msg)

    acquistionMeanOccupancy = acquistionMeanOccupancy/acquisitionCount
    tAquisitionStartFormattedTimeStamp = timezone.formatTimeStampLong(tAquisitionStart, tzId)
    tAquisitionEndFormattedTimeStamp = timezone.formatTimeStampLong(tAquisitionEnd, tzId)
    meanOccupancy = meanOccupancy / nreadings
    retval = {"status":"OK",\
        "minOccupancy":minOccupancy, \
        "tAquistionStart": tAquisitionStart, \
        "tAquisitionStartFormattedTimeStamp": tAquisitionStartFormattedTimeStamp, \
        "tAquisitionEnd":tAquisitionEnd, \
        "tAquisitionEndFormattedTimeStamp": tAquisitionEndFormattedTimeStamp, \
        "tStartReadings":minTime, \
        "tStartLocalTime": minLocalTime, \
        "tStartLocalTimeFormattedTimeStamp" : timezone.formatTimeStampLong(minTime, tzId), \
        "tStartDayBoundary":tStartDayBoundary, \
        "tEndReadings":maxTime, \
        "tEndReadingsLocalTime":tEndReadingsLocalTime, \
        "tEndLocalTimeFormattedTimeStamp" : timezone.formatTimeStampLong(maxTime, tzId), \
        "tEndDayBoundary":tEndDayBoundary, \
        "maxOccupancy":util.roundTo3DecimalPlaces(maxOccupancy), \
        "meanOccupancy":util.roundTo3DecimalPlaces(meanOccupancy), \
        "maxFreq":maxFreq, \
        "minFreq":minFreq, \
        "measurementType": measurementType, \
        "acquistionCount":acquisitionCount, \
        "acquistionMaxOccupancy":util.roundTo3DecimalPlaces(acquistionMaxOccupancy),\
        "acquistionMinOccupancy":util.roundTo3DecimalPlaces(acquistionMinOccupancy),\
        "aquistionMeanOccupancy":util.roundTo3DecimalPlaces(acquistionMeanOccupancy),\
        "readingsCount":nreadings}
    return jsonify(retval)

def getAcquistionCount(sensorId,sys2detect,minfreq, maxfreq,tAcquistionStart,dayCount):
    freqRange = msgutils.freqRange(sys2detect,minfreq,maxfreq)
    query = {SENSOR_ID: sensorId, "t":{"$gte":tAcquistionStart},FREQ_RANGE:freqRange}
    msg = DbCollections.getDataMessages(sensorId).find_one(query)
    startTime = msgutils.getDayBoundaryTimeStamp(msg)
    endTime = startTime + SECONDS_PER_DAY * dayCount
    query = {SENSOR_ID: sensorId, "t":{"$gte":startTime}, "t":{"$lte":endTime},FREQ_RANGE:freqRange}
    cur = DbCollections.getDataMessages(sensorId).find(query)
    count = 0
    if cur != None:
       count = cur.count()
    retval = {"count":count}
    return jsonify(retval)

def recomputeOccupancies(sensorId):  
    if SessionLock.isAcquired() :
        return {"status":"NOK","StatusMessage":"Session is locked. Try again later."}
    SessionLock.acquire()
    try :
        dataMessages = DbCollections.getDataMessages(sensorId).find({SENSOR_ID:sensorId})
        if dataMessages == None:
            return {"status":"OK", "StatusMessage":"No Data Found"}
        for jsonData in dataMessages:
            if DataMessage.resetThreshold(jsonData):
                DbCollections.getDataMessages(sensorId).update({"_id":jsonData["_id"]},{"$set":jsonData},upsert=False)
                lastLocationPost = msgutils.getLocationMessage(jsonData)
                if not "maxOccupancy" in lastLocationPost:
                    if jsonData["mType"] == SWEPT_FREQUENCY:
                        lastLocationPost["maxOccupancy"]  = jsonData["occupancy"]
                        lastLocationPost["minOccupancy"]  = jsonData["occupancy"]
                    else:
                        lastLocationPost["maxOccupancy"]  = jsonData["maxOccupancy"]
                        lastLocationPost["minOccupancy"]  = jsonData["minOccupancy"]
                else:
                    if DataMessage.getMeasurementType(jsonData) == SWEPT_FREQUENCY:
                        lastLocationPost["maxOccupancy"] = np.maximum(lastLocationPost["maxOccupancy"],jsonData["occupancy"])
                        lastLocationPost["minOccupancy"] = np.minimum(lastLocationPost["minOccupancy"],jsonData["occupancy"])
                    else:
                        lastLocationPost["maxOccupancy"] = np.maximum(lastLocationPost["maxOccupancy"],jsonData["maxOccupancy"])
                        lastLocationPost["minOccupancy"] = np.minimum(lastLocationPost["minOccupancy"],jsonData["minOccupancy"])
                DbCollections.getLocationMessages().update({"_id": lastLocationPost["_id"]}, {"$set":lastLocationPost}, upsert=False)
            else:
                util.debugPrint("Threshold is unchanged -- not resetting")
        return {"status":"OK","sensors":SensorDb.getAllSensors()}
    finally:
        SessionLock.release()

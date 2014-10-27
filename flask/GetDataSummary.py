import flaskr as main
import populate_db
from flask import request,make_response,jsonify,abort
import timezone
import util
import numpy as np
import time
import pymongo
import msgutils

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
        freqRange = populate_db.freqRange(sys2detect,minFreq, maxFreq)
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
    tzId = locationMessage[main.TIME_ZONE_KEY]
    query = { main.SENSOR_ID: sensorId, "locationMessageId":locationMessageId }
    msg = main.db.dataMessages.find_one(query)
    measurementType = msg["mType"]
    if msg == None:
        abort(404)
    if tmin == '' and dayCount == '':
        query = { main.SENSOR_ID: sensorId, "locationMessageId":locationMessageId }
        tmin = msgutils.getDayBoundaryTimeStamp(msg)
        if measurementType == "FFT-Power":
           dayCount = 14
        else:
           dayCount = 30
        mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin), tzId)
        maxtime = mintime + int(dayCount) * main.SECONDS_PER_DAY
    elif tmin != ''  and dayCount == '' :
        mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin), tzId)
        if measurementType == "FFT-Power":
           dayCount = 14
        else:
           dayCount = 30
        mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin), tzId)
        maxtime = mintime + int(dayCount) * main.SECONDS_PER_DAY
    else:
        mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin), tzId)
        maxtime = mintime + int(dayCount) * main.SECONDS_PER_DAY

    if freqRange == None:
        query = { main.SENSOR_ID: sensorId, "locationMessageId":locationMessageId, \
                     "t": { '$lte':maxtime, '$gte':mintime}  }
    else:
        query = { main.SENSOR_ID: sensorId, "locationMessageId":locationMessageId, \
                 "t": { '$lte':maxtime, '$gte':mintime}, "freqRange":freqRange }

    util.debugPrint(query)
    cur = main.db.dataMessages.find(query)
    if cur == None:
        errorStr = "No data found"
        response = make_response(util.formatError(errorStr), 404)
        return response
    nreadings = cur.count()
    cur.sort('t',pymongo.ASCENDING)
    if nreadings == 0:
        util.debugPrint("No data found. zero cur count.")
        del query['t']
        msg = main.db.dataMessages.find_one(query)
        if msg != None:
            tStartDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg["t"], tzId)
            if dayCount == '':
                query["t"] = {"$gte":tStartDayBoundary}
            else:
                maxtime = tStartDayBoundary + int(dayCount) * main.SECONDS_PER_DAY
                query["t"] = {"$gte":tStartDayBoundary, "$lte":maxtime}
            cur = main.db.dataMessages.find(query)
            nreadings = cur.count()
        else :
            errorStr = "No data found"
            response = make_response(util.formatError(errorStr), 404)
            return response


    util.debugPrint("retrieved " + str(nreadings))
    cur.batch_size(20)
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
        if tStartDayBoundary == 0 :
            tStartDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg["t"], tzId)
            (minLocalTime, tStartLocalTimeTzName) = timezone.getLocalTime(msg['t'], tzId)
        if msg["mType"] == "FFT-Power" :
            minOccupancy = np.minimum(minOccupancy, msg["minOccupancy"])
            maxOccupancy = np.maximum(maxOccupancy, msg["maxOccupancy"])
        else:
            minOccupancy = np.minimum(minOccupancy, msg["occupancy"])
            maxOccupancy = np.maximum(maxOccupancy, msg["occupancy"])
        maxFreq = np.maximum(msg["mPar"]["fStop"], maxFreq)
        if minFreq == -1 :
            minFreq = msg["mPar"]["fStart"]
        else:
            minFreq = np.minimum(msg["mPar"]["fStart"], minFreq)
        if "meanOccupancy" in msg:
            meanOccupancy += msg["meanOccupancy"]
        else:
            meanOccupancy += msg["occupancy"]
        minTime = int(np.minimum(minTime, msg["t"]))
        maxTime = np.maximum(maxTime, msg["t"])
        lastMessage = msg
    (tEndReadingsLocalTime, tEndReadingsLocalTimeTzName) = timezone.getLocalTime(lastMessage['t'], tzId)
    tEndDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(lastMessage["t"], tzId)
    # now get the global min and max time of the aquistions.
    if 't' in query:
        del query['t']

    cur = main.db.dataMessages.find(query)
    acquisitionCount = cur.count()
    sortedCur = cur.sort('t',pymongo.ASCENDING)
    firstMessage = sortedCur.next()
    tAquisitionStart = firstMessage['t']

    cur = main.db.dataMessages.find(query)
    sortedCur = cur.sort('t', pymongo.DESCENDING)
    lastMessage = sortedCur.next()
    tAquisitionEnd = lastMessage['t']

    cur = main.db.dataMessages.find(query)
    acquistionMaxOccupancy = -1000
    acquistionMinOccupancy = 1000
    acquistionMeanOccupancy = 0
    for msg in cur :
        acquistionMaxOccupancy = np.maximum(acquistionMaxOccupancy,msg["occupancy"])
        acquistionMinOccupancy = np.minimum(acquistionMinOccupancy,msg["occupancy"])
        acquistionMeanOccupancy = acquistionMeanOccupancy + msg["occupancy"]
    acquistionMeanOccupancy = acquistionMeanOccupancy/acquisitionCount
    tAquisitionStartFormattedTimeStamp = timezone.formatTimeStampLong(tAquisitionStart, tzId)
    tAquisitionEndFormattedTimeStamp = timezone.formatTimeStampLong(tAquisitionEnd, tzId)
    meanOccupancy = meanOccupancy / nreadings
    retval = {"minOccupancy":minOccupancy, \
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
    freqRange = populate_db.freqRange(sys2detect,minfreq,maxfreq)
    query = {main.SENSOR_ID: sensorId, "t":{"$gte":tAcquistionStart},"freqRange":freqRange}
    msg = main.db.dataMessages.find_one(query)
    startTime = msgutils.getDayBoundaryTimeStamp(msg)
    endTime = startTime + main.SECONDS_PER_DAY * dayCount
    query = {main.SENSOR_ID: sensorId, "t":{"$gte":startTime}, "t":{"$lte":endTime},"freqRange":freqRange}
    cur = main.db.dataMessages.find(query)
    count = 0
    if cur != None:
       count = cur.count()
    retval = {"count":count}
    return jsonify(retval)

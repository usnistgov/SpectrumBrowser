import flaskr as main
import populate_db
from flask import request,make_response,jsonify,abort
import timezone
import util
import numpy as np
import time
import pymongo

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
    if freqRange == None:
        if tmin == '' and dayCount == '':
            query = { main.SENSOR_ID: sensorId, "locationMessageId":locationMessageId }
        elif tmin != ''  and dayCount == '' :
            mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin), tzId)
            query = { main.SENSOR_ID:sensorId, "locationMessageId":locationMessageId, "t" : {'$gte':mintime} }
        else:
            mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin), tzId)
            maxtime = mintime + int(dayCount) * main.SECONDS_PER_DAY
            query = { main.SENSOR_ID: sensorId, "locationMessageId":locationMessageId, "t": { '$lte':maxtime, '$gte':mintime}  }
    else :
        if tmin == '' and dayCount == '':
            query = { main.SENSOR_ID: sensorId, "locationMessageId":locationMessageId, "freqRange": freqRange }
        elif tmin != ''  and dayCount == '' :
            mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin), tzId)
            query = { main.SENSOR_ID:sensorId, "locationMessageId":locationMessageId, "t" : {'$gte':mintime}, "freqRange":freqRange }
        else:
            mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin), tzId)
            maxtime = mintime + int(dayCount) * main.SECONDS_PER_DAY
            query = { main.SENSOR_ID: sensorId, "locationMessageId":locationMessageId, "t": { '$lte':maxtime, '$gte':mintime} , "freqRange":freqRange }

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
    measurementType = "UNDEFINED"
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
        minTime = np.minimum(minTime, msg["t"])
        maxTime = np.maximum(maxTime, msg["t"])
        measurementType = msg["mType"]
        lastMessage = msg
    (tEndReadingsLocalTime, tEndReadingsLocalTimeTzName) = timezone.getLocalTime(lastMessage['t'], tzId)
    tEndDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(lastMessage["t"], tzId)
    # now get the global min and max time of the aquistions.
    if 't' in query:
        del query['t']
    cur = main.db.dataMessages.find(query)
    sortedCur = cur.sort('t',pymongo.ASCENDING)
    firstMessage = sortedCur.next()
    cur = main.db.dataMessages.find(query)
    sortedCur = cur.sort('t', pymongo.DESCENDING)
    lastMessage = sortedCur.next()
    tAquisitionStart = firstMessage['t']
    tAquisitionEnd = lastMessage['t']
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
        "tStartDayBoundary":float(tStartDayBoundary), \
        "tEndReadings":float(maxTime), \
        "tEndReadingsLocalTime":float(tEndReadingsLocalTime), \
        "tEndLocalTimeFormattedTimeStamp" : timezone.formatTimeStampLong(maxTime, tzId), \
        "tEndDayBoundary":float(tEndDayBoundary), \
        "maxOccupancy":util.roundTo3DecimalPlaces(maxOccupancy), \
        "meanOccupancy":util.roundTo3DecimalPlaces(meanOccupancy), \
        "maxFreq":maxFreq, \
        "minFreq":minFreq, \
        "measurementType": measurementType, \
        "readingsCount":float(nreadings)}
    return jsonify(retval)

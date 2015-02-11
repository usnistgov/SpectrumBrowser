import util
import timezone
import populate_db
from flask import abort,jsonify
import msgutils
from Defines import SECONDS_PER_DAY,TIME_ZONE_KEY,SENSOR_ID
import DbCollections

def getOneDayStats(sensorId,startTime,sys2detect,minFreq,maxFreq):
    """
    Generate and return a JSON structure with the one day statistics.

    startTime is the start time in UTC
    sys2detect is the system to detect.
    minFreq is the minimum frequency of the frequency band of interest.
    maxFreq is the maximum frequency of the frequency band of interest.

    """
    freqRange = msgutils.freqRange(sys2detect,minFreq, maxFreq)
    mintime = int(startTime)
    maxtime = mintime + SECONDS_PER_DAY
    query = { SENSOR_ID: sensorId, "t": { '$lte':maxtime, '$gte':mintime}, "freqRange":freqRange  }
    util.debugPrint(query)
    msg = DbCollections.getDataMessages().find_one(query)
    locationMessage = msgutils.getLocationMessage(msg)
    tzId = locationMessage[TIME_ZONE_KEY]
    mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg["t"], tzId)
    maxtime = mintime + SECONDS_PER_DAY
    query = { SENSOR_ID: sensorId, "t": { '$lte':maxtime, '$gte':mintime} , "freqRange":freqRange }
    cur = DbCollections.getDataMessages().find(query)
    if cur == None:
        abort(404)
    res = {}
    values = {}
    res["formattedDate"] = timezone.formatTimeStampLong(mintime, locationMessage[TIME_ZONE_KEY])
    acquisitionCount = cur.count()
    prevMsg = None
    for msg in cur:
        if prevMsg == None:
            prevMsg = msgutils.getPrevAcquisition(msg)
        channelCount = msg["mPar"]["n"]
        measurementsPerAcquisition = msg["nM"]
        cutoff = msg["cutoff"]
        values[int(msg["t"] - mintime)] = {"t": msg["t"], \
                        "maxPower" : msg["maxPower"], \
                        "minPower" : msg["minPower"], \
                        "maxOccupancy":util.roundTo3DecimalPlaces(msg["maxOccupancy"]), \
                        "minOccupancy":util.roundTo3DecimalPlaces(msg["minOccupancy"]), \
                        "meanOccupancy":util.roundTo3DecimalPlaces(msg["meanOccupancy"]), \
                        "medianOccupancy":util.roundTo3DecimalPlaces(msg["medianOccupancy"])}
    query = { SENSOR_ID: sensorId, "t": {'$gt':maxtime} , "freqRange":freqRange }
    msg = DbCollections.getDataMessages().find_one(query)
    if msg != None:
        nextDay = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg['t'],tzId)
    else:
        nextDay = mintime
    if prevMsg != None:
        prevDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(prevMsg['t'],tzId)
        query = { SENSOR_ID: sensorId, "t": {'$gte':prevDayBoundary} , "freqRange":freqRange }
        msg = DbCollections.getDataMessages().find_one(query)
        prevDay = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg['t'],tzId)
    else:
        prevDay = mintime
    res['nextIntervalStart'] = nextDay
    res['prevIntervalStart'] = prevDay
    res['currentIntervalStart'] = mintime
    res["channelCount"] = channelCount
    res["measurementsPerAcquisition"] = measurementsPerAcquisition
    res["acquisitionCount"] = acquisitionCount
    res["cutoff"] = cutoff
    res["values"] = values
    return jsonify(res)


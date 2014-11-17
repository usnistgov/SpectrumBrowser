import flaskr
import util
import timezone
import populate_db
from flask import abort,jsonify
from bson.objectid import ObjectId

def getOneDayStats(sensorId,startTime,sys2detect,minFreq,maxFreq):
    """
    Generate and return a JSON structure with the one day statistics.

    startTime is the start time in UTC
    sys2detect is the system to detect.
    minFreq is the minimum frequency of the frequency band of interest.
    maxFreq is the maximum frequency of the frequency band of interest.

    """
    freqRange = populate_db.freqRange(sys2detect,minFreq, maxFreq)
    mintime = int(startTime)
    maxtime = mintime + flaskr.SECONDS_PER_DAY
    query = { flaskr.SENSOR_ID: sensorId, "t": { '$lte':maxtime, '$gte':mintime}, "freqRange":freqRange  }
    util.debugPrint(query)
    msg = flaskr.db.dataMessages.find_one(query)
    query = { "_id": ObjectId(msg["locationMessageId"]) }
    locationMessage = flaskr.db.locationMessages.find_one(query)
    tzId = locationMessage[flaskr.TIME_ZONE_KEY]
    mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg["t"], tzId)
    maxtime = mintime + flaskr.SECONDS_PER_DAY
    query = { flaskr.SENSOR_ID: sensorId, "t": { '$lte':maxtime, '$gte':mintime} , "freqRange":freqRange }
    cur = flaskr.db.dataMessages.find(query)
    if cur == None:
        abort(404)
    res = {}
    values = {}
    res["formattedDate"] = timezone.formatTimeStampLong(mintime, locationMessage[flaskr.TIME_ZONE_KEY])
    acquisitionCount = cur.count()
    for msg in cur:
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
    query = { flaskr.SENSOR_ID: sensorId, "t": {'$gt':maxtime} , "freqRange":freqRange }
    msg = flaskr.db.dataMessages.find_one(query)
    if msg != None:
        nextDay = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg['t'],tzId)
    else:
        nextDay = mintime

    query = { flaskr.SENSOR_ID: sensorId, "t": {'$gt':mintime - flaskr.SECONDS_PER_DAY} , "freqRange":freqRange }
    msg = flaskr.db.dataMessages.find_one(query)
    prevDay = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg['t'],tzId)
    res['nextIntervalStart'] = nextDay
    res['prevIntervalStart'] = prevDay
    res['currentIntervalStart'] = mintime
    res["channelCount"] = channelCount
    res["measurementsPerAcquisition"] = measurementsPerAcquisition
    res["acquisitionCount"] = acquisitionCount
    res["cutoff"] = cutoff
    res["values"] = values
    return jsonify(res)


import util
import timezone
import msgutils
from Defines import SECONDS_PER_DAY,TIME_ZONE_KEY,SENSOR_ID,FREQ_RANGE, STATUS,ERROR_MESSAGE,OK,NOK
from Defines import CHANNEL_COUNT
from Defines import ACQUISITION_COUNT
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
    query = { SENSOR_ID: sensorId, "t": { "$lte":maxtime, "$gte":mintime}, FREQ_RANGE:freqRange  }
    util.debugPrint(query)
    msg = DbCollections.getDataMessages(sensorId).find_one(query)
    if msg == None:
        return {STATUS:NOK, ERROR_MESSAGE: "Data message not found"}
    locationMessage = msgutils.getLocationMessage(msg)
    tzId = locationMessage[TIME_ZONE_KEY]
    mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg["t"], tzId)
    maxtime = mintime + SECONDS_PER_DAY
    query = { SENSOR_ID: sensorId, "t": { "$lte":maxtime, "$gte":mintime} , FREQ_RANGE:freqRange }
    cur = DbCollections.getDataMessages(sensorId).find(query)
    if cur == None:
        return {STATUS:NOK, ERROR_MESSAGE: "Data messages not found"}
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
    query = { SENSOR_ID: sensorId, "t": {"$gt":maxtime} , FREQ_RANGE:freqRange }
    msg = DbCollections.getDataMessages(sensorId).find_one(query)
    if msg != None:
        nextDay = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg["t"],tzId)
    else:
        nextDay = mintime
    if prevMsg != None:
        prevDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(prevMsg["t"],tzId)
        query = { SENSOR_ID: sensorId, "t": {"$gte":prevDayBoundary} , FREQ_RANGE:freqRange }
        msg = DbCollections.getDataMessages(sensorId).find_one(query)
        prevDay = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg["t"],tzId)
    else:
        prevDay = mintime
    res["nextIntervalStart"] = nextDay
    res["prevIntervalStart"] = prevDay
    res["currentIntervalStart"] = mintime
    res[CHANNEL_COUNT] = channelCount
    res["measurementsPerAcquisition"] = measurementsPerAcquisition
    res[ACQUISITION_COUNT] = acquisitionCount
    res["cutoff"] = cutoff
    res["values"] = values
    res[STATUS] = OK
    return res


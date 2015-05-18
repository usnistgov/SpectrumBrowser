import timezone
import util
import numpy as np
import time
import pymongo
import msgutils
from Defines import TIME_ZONE_KEY,SENSOR_ID,SECONDS_PER_DAY,\
    FFT_POWER, SWEPT_FREQUENCY,FREQ_RANGE, THRESHOLDS,SYSTEM_TO_DETECT,\
    COUNT, MIN_FREQ_HZ, MAX_FREQ_HZ, BAND_STATISTICS, STATUS, TIME
import DbCollections
import DataMessage
import Message
import SensorDb
import SessionLock
import Sensor


def getSensorDataSummary(sensorId,locationMessage):
    tzId = locationMessage[TIME_ZONE_KEY]
    locationMessageId = str(locationMessage["_id"])
    query = { SENSOR_ID: sensorId, "locationMessageId":locationMessageId }
    msg = DbCollections.getDataMessages(sensorId).find_one(query)
    if msg == None:
        util.errorPrint(query)
        return {STATUS:"NOK","ErrorMessage":"No Data Message Matching that Location Message"}
    
    cur = DbCollections.getDataMessages(sensorId).find(query)
    acquisitionCount = cur.count()
    sortedCur = cur.sort('t',pymongo.ASCENDING)
    firstMessage = sortedCur.next()
    measurementType = DataMessage.getMeasurementType(firstMessage)
    
    minTime = locationMessage["firstDataMessageTimeStamp"] 
    maxTime = locationMessage["lastDataMessageTimeStamp"]  
    maxOccupancy = locationMessage["maxOccupancy"]
    minOccupancy = locationMessage["minOccupancy"]
    
    tStartDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(minTime, tzId)
    (minLocalTime, tStartLocalTimeTzName) = timezone.getLocalTime(msg['t'], tzId)
    cur = DbCollections.getDataMessages(sensorId).find(query)
    count = cur.count()
    # Compute the min max occupancies for all the messages stored by the sensor. 
  
    
    tEndDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(maxTime, tzId)
    
    retval = {"status":"OK",\
        "minOccupancy":minOccupancy, \
        "tStartReadings":minTime, \
        "tStartLocalTime": minLocalTime, \
        "tStartLocalTimeFormattedTimeStamp" : timezone.formatTimeStampLong(minTime, tzId), \
        "tStartDayBoundary":tStartDayBoundary, \
        "tEndDayBoundary":tEndDayBoundary,\
        "tEndReadings":maxTime, \
        "tEndLocalTimeFormattedTimeStamp" : timezone.formatTimeStampLong(maxTime, tzId), \
        "maxOccupancy":maxOccupancy, \
      
        "measurementType": measurementType, \
        COUNT:acquisitionCount}
    
    
    return retval

def getBandDataSummary(sensorId,locationMessage, sys2detect, minFreq,maxFreq, mintime,dayCount = None):
    tzId = locationMessage[TIME_ZONE_KEY]
    locationMessageId = str(locationMessage["_id"])
    query = { SENSOR_ID: sensorId, "locationMessageId":locationMessageId }
    msg = DbCollections.getDataMessages(sensorId).find_one(query)
    if msg == None:
        return {"status":"NOK","ErrorMessage":"No Location Message"}
    
    measurementType = DataMessage.getMeasurementType(msg)
    freqRange = msgutils.freqRange(sys2detect,minFreq,maxFreq)
    if dayCount == None :
        query = { SENSOR_ID: sensorId, "locationMessageId":locationMessageId, \
                     "t": {  '$gte':mintime} , FREQ_RANGE:freqRange }
    else:
        maxtime = mintime + int(dayCount) * SECONDS_PER_DAY
        query = { SENSOR_ID: sensorId, "locationMessageId":locationMessageId, \
                     "t": { '$lte':maxtime, '$gte':mintime} , FREQ_RANGE:freqRange }
    util.debugPrint(query)
    cur = DbCollections.getDataMessages(sensorId).find(query)
    count = 0
    if cur == None or cur.count() == 0:
        return {FREQ_RANGE:freqRange, COUNT:0}
    else:
        count = cur.count()
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
        tStartDayBoundary = 0
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
            maxTime = int(np.maximum(maxTime, Message.getTime(msg)))
        meanOccupancy = meanOccupancy / count
        (tEndReadingsLocalTime, tEndReadingsLocalTimeTzName) = timezone.getLocalTime(maxTime, tzId)
        tEndDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(maxTime, tzId)
        tStartDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(minTime, tzId)
        retval = {"tStartDayBoundary":tStartDayBoundary, \
                  "tEndDayBoundary":tEndDayBoundary, \
                  "tStartReadings":minTime, \
                  "tStartLocalTime": minLocalTime, \
                  "tStartLocalTimeFormattedTimeStamp" : timezone.formatTimeStampLong(minTime, tzId), \
                  "tEndReadings":maxTime, \
                  "tEndReadingsLocalTime":tEndReadingsLocalTime, \
                  "tEndLocalTimeFormattedTimeStamp" : timezone.formatTimeStampLong(maxTime, tzId), \
                  "tEndDayBoundary":tEndDayBoundary,\
                  "maxOccupancy": maxOccupancy, \
                  "meanOccupancy":meanOccupancy, \
                  "minOccupancy":minOccupancy, \
                  "maxFreq":maxFreq, \
                  "minFreq":minFreq,\
                  SYSTEM_TO_DETECT:sys2detect,\
                  "measurementType":measurementType,\
                  COUNT:count
                  }
        return retval

def getDataSummaryForAllBands(sensorId, locationMessage, tmin = None, dayCount = None):
    """
    get the summary of the data corresponding to the location message.
    """
     # tmin and tmax specify the min and the max values of the time range of interest.
    locationMessageId = str(locationMessage["_id"])
   
    tzId = locationMessage[TIME_ZONE_KEY]
    query = { SENSOR_ID: sensorId, "locationMessageId":locationMessageId }
    msg = DbCollections.getDataMessages(sensorId).find_one(query)
    if msg == None:
        util.errorPrint("Not Found " + str(query))
        return {"status":"NOK","ErrorMessage":"No Location Message"}
  
    measurementType = DataMessage.getMeasurementType(msg)
    if tmin == None and dayCount == None:
        query = {SENSOR_ID: sensorId, "locationMessageId":locationMessageId }
        tmin = msgutils.getDayBoundaryTimeStamp(msg)
        mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin), tzId)
    elif tmin != None  and dayCount == None :
        mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin), tzId)
    else:
        mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin), tzId)
      
        
        
    sensor = SensorDb.getSensor(sensorId)
    bands = sensor[THRESHOLDS]
    bandStatistics = []
    for key in bands.keys():
        band = bands[key]
        minFreq = band[MIN_FREQ_HZ]
        maxFreq = band[MAX_FREQ_HZ]
        sys2detect = band[SYSTEM_TO_DETECT]
        bandSummary = getBandDataSummary(sensorId,locationMessage, sys2detect, minFreq,maxFreq, mintime,dayCount=dayCount)
        bandStatistics.append(bandSummary)   
    
    return bandStatistics;
    

def getDataSummary(sensorId,locationMessage,tmin=None,dayCount=None):
    
    retval = getSensorDataSummary(sensorId,locationMessage)
    if retval[STATUS] == "OK" :
        retval[BAND_STATISTICS] = getDataSummaryForAllBands(sensorId, locationMessage,tmin=tmin,dayCount=dayCount)
    return retval
    


def getAcquistionCount(sensorId,sys2detect,minfreq, maxfreq,tAcquistionStart,dayCount):
    freqRange = msgutils.freqRange(sys2detect,minfreq,maxfreq)
    query = {SENSOR_ID: sensorId, "t":{"$gte":tAcquistionStart},FREQ_RANGE:freqRange}
    msg = DbCollections.getDataMessages(sensorId).find_one(query)
    if msg == None:
        retval = {COUNT:0}
        retval[STATUS]  = "OK"
        return retval
    
    
    startTime = msgutils.getDayBoundaryTimeStamp(msg)

    if dayCount > 0:
        endTime = startTime + SECONDS_PER_DAY * dayCount
        query = {SENSOR_ID: sensorId, TIME:{"$gte":startTime}, TIME:{"$lte":endTime},FREQ_RANGE:freqRange}
    else:
        query = {SENSOR_ID: sensorId, TIME:{"$gte":startTime},FREQ_RANGE:freqRange}

    cur = DbCollections.getDataMessages(sensorId).find(query)
    count = cur.count()
        
    cur.sort(TIME,pymongo.DESCENDING)
    lastMessage = cur.next()
    endTime = msgutils.getDayBoundaryTimeStamp(lastMessage)
    
    
    retval = {COUNT:count}
    retval["tStartReadings"] = msg[TIME]
    retval["tEndReadings"] = lastMessage[TIME]
    retval["tStartDayBoundary"] = startTime
    retval["tEndDayBoundary"] = endTime
    
    retval[STATUS]  = "OK"
    return retval

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

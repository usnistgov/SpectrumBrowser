import numpy as np
import struct
import util
import flaskr as main
import msgutils
import pymongo
import timezone
from bson.objectid import ObjectId
import gridfs
import populate_db



# Message utilities.


def getMaxMinFreq(msg):
    """
    Get the max and min frequencies from a message.
    """
    return (msg["mPar"]["fStop"], msg["mPar"]["fStart"])

def getCalData(systemMessage) :
    """
    Get the data associated with a Cal message.
    """
    if not "Cal" in systemMessage:
        return None
    msg = systemMessage["Cal"]
    if  msg != "N/A" :
        sensorId = systemMessage[main.SENSOR_ID]
        fs = gridfs.GridFS(main.db,sensorId + "/data")
        messageBytes = fs.get(ObjectId(msg["dataKey"])).read()
        nM = msg["nM"]
        n = msg["mPar"]["n"]
        lengthToRead = nM*n
        if lengthToRead == None:
            util.debugPrint("No data to read")
            return None
        if msg["DataType"] == "ASCII":
            powerVal = eval(messageBytes)
        elif msg["DataType"] == "Binary - int8":
            powerVal = np.array(np.zeros(n*nM))
            for i in range(0,lengthToRead):
                powerVal[i] = float(struct.unpack('b',messageBytes[i:i+1])[0])
        elif msg["DataType"] == "Binary - int16":
            powerVal = np.array(np.zeros(n*nM))
            for i in range(0,lengthToRead,2):
                powerVal[i] = float(struct.unpack('h',messageBytes[i:i+2])[0])
        elif msg["DataType"] == "Binary - float32":
            powerVal = np.array(np.zeros(n*nM))
            for i in range(0,lengthToRead,4):
                powerVal[i] = float(struct.unpack('f',messageBytes[i:i+4])[0])
        return powerVal
    else:
        return None

# Extract data from a data message
def getData(msg) :
    """
    get the data associated with a data message.
    """
    fs = gridfs.GridFS(main.db,msg[main.SENSOR_ID]+ "/data")
    messageBytes = fs.get(ObjectId(msg["dataKey"])).read()
    nM = msg["nM"]
    n = msg["mPar"]["n"]
    lengthToRead = nM*n
    if lengthToRead == None:
        util.debugPrint("No data to read")
        return None
    if msg["DataType"] == "ASCII":
        powerVal = eval(messageBytes)
    elif msg["DataType"] == "Binary - int8":
        powerVal = np.array(np.zeros(n*nM))
        for i in range(0,lengthToRead):
            powerVal[i] = float(struct.unpack('b',messageBytes[i:i+1])[0])
    elif msg["DataType"] == "Binary - int16":
        powerVal = np.array(np.zeros(n*nM))
        for i in range(0,lengthToRead,2):
            powerVal[i] = float(struct.unpack('h',messageBytes[i:i+2])[0])
    elif msg["DataType"] == "Binary - float32":
        powerVal = np.array(np.zeros(n*nM))
        for i in range(0,lengthToRead,4):
            powerVal[i] = float(struct.unpack('f',messageBytes[i:i+4])[0])
    return powerVal

def getMaxPower(msg):
    """
    Get the max power for the acquistions associated with this msg.
    """
    locationMessage = getLocationMessage(msg)
    return locationMessage["maxPower"]

def getMinPower(msg):
    """
    Get the max power for the acquistions associated with this msg.
    """
    locationMessage = getLocationMessage(msg)
    return locationMessage["minPower"]

def getGlobalMaxOccupancy(msg):
    locationMessage = getLocationMessage(msg)
    return locationMessage["maxOccupancy"]

def getGlobalMinOccupancy(msg):
    locationMessage = getLocationMessage(msg)
    return locationMessage["minOccupancy"]

def getMinDayBoundaryForAcquistions(msg):
    """
    Get the minimum day boundary for acquistions assocaiated with this msg.
    """
    locationMsg = getLocationMessage(msg)
    timeStamp = locationMsg["firstDataMessageTimeStamp"]
    tzId = msg[main.TIME_ZONE_KEY]
    return timezone.getDayBoundaryTimeStampFromUtcTimeStamp(timeStamp,tzId)

def getLocationMessage(msg):
    """
    get the location message corresponding to a data message.
    """
    return main.db.locationMessages.find_one({main.SENSOR_ID:msg[main.SENSOR_ID], "t": {"$lte":msg["t"]}})

def getNextAcquisition(msg):
    """
    get the next acquisition for this message or None if none found.
    """
    query = {main.SENSOR_ID: msg[main.SENSOR_ID], "t":{"$gt": msg["t"]}, "freqRange":msg['freqRange']}
    return main.db.dataMessages.find_one(query)

def getPrevAcquisition(msg):
    """
    get the prev acquisition for this message or None if none found.
    """
    query = {main.SENSOR_ID: msg[main.SENSOR_ID], "t":{"$lt": msg["t"]}, "freqRange":msg["freqRange"]}
    cur = main.db.dataMessages.find(query)
    if cur == None or cur.count() == 0:
        return None
    sortedCur = cur.sort('t', pymongo.DESCENDING).limit(10)
    return sortedCur.next()

def getLastAcquisition(sensorId,sys2detect,minFreq,maxFreq):
    """
    get the last acquisiton of the collection.
    """
    query = {main.SENSOR_ID:sensorId,"freqRange":populate_db.freqRange(sys2detect,minFreq,maxFreq)}
    util.debugPrint(query)
    cur = main.db.dataMessages.find(query)
    if cur == None or cur.count() == 0:
        return None
    sortedCur = cur.sort('t', pymongo.DESCENDING).limit(10)
    return sortedCur.next()

def getLastAcquisitonTimeStamp(sensorId,sys2detect,minFreq,maxFreq):
    """
    get the time of the last aquisition of the collection.
    """
    msg = getLastAcquisition(sensorId,sys2detect,minFreq,maxFreq)
    if msg == None:
        return -1
    else:
        return msg['t']

def getLastSensorAcquisitionTimeStamp(sensorId):
    """
    get the last capture from the sensor, given its ID.
    """
    cur  = main.db.locationMessages.find({"SensorID":sensorId})
    if cur == None or cur.count()  == 0:
        return -1
    else:
        sortedCur = cur.sort('t', pymongo.DESCENDING).limit(10)
        locationMessage = sortedCur.next()
        return locationMessage["lastDataMessageTimeStamp"]

def getPrevDayBoundary(msg):
    """
    get the previous acquisition day boundary.
    """
    prevMsg = getPrevAcquisition(msg)
    if prevMsg == None:
        locationMessage = getLocationMessage(msg)
        return  timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg['t'], locationMessage[main.TIME_ZONE_KEY])
    locationMessage = msgutils.getLocationMessage(prevMsg)
    timeZone = locationMessage[main.TIME_ZONE_KEY]
    return timezone.getDayBoundaryTimeStampFromUtcTimeStamp(prevMsg['t'], timeZone)

def getDayBoundaryTimeStamp(msg):
    """
    Get the universal time stamp for the day boundary of this message.
    """
    locationMessage = getLocationMessage(msg)
    timeZone = locationMessage[main.TIME_ZONE_KEY]
    return timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg['t'], timeZone)


def getNextDayBoundary(msg):
    """
    get the next acquistion day boundary.
    """
    nextMsg = getNextAcquisition(msg)
    if nextMsg == None:
        locationMessage = getLocationMessage(msg)
        return  timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg['t'], locationMessage[main.TIME_ZONE_KEY])
    locationMessage = getLocationMessage(nextMsg)
    timeZone = locationMessage[main.TIME_ZONE_KEY]
    nextDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(nextMsg['t'], timeZone)
    if main.debug:
        thisDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg['t'], locationMessage[main.TIME_ZONE_KEY])
        print "getNextDayBoundary: dayBoundary difference ", (nextDayBoundary - thisDayBoundary) / 60 / 60
    return nextDayBoundary

def trimSpectrumToSubBand(msg, subBandMinFreq, subBandMaxFreq):
    """
    Trim spectrum to a sub band of a measurement band.
    """
    data = msgutils.getData(msg)
    n = msg["mPar"]["n"]
    minFreq = msg["mPar"]["fStart"]
    maxFreq = msg["mPar"]["fStop"]
    freqRangePerReading = float(maxFreq - minFreq) / float(n)
    endReadingsToIgnore = int((maxFreq - subBandMaxFreq) / freqRangePerReading)
    topReadingsToIgnore = int((subBandMinFreq - minFreq) / freqRangePerReading)
    powerArray = np.array([data[i] for i in range(topReadingsToIgnore, n - endReadingsToIgnore)])
    # util.debugPrint("Length " + str(len(powerArray)))
    return powerArray

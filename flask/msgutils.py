import numpy as np
import struct
import util
import flaskr as globals
import msgutils
import pymongo
import timezone
from bson.objectid import ObjectId



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
        sensorId = systemMessage[globals.SENSOR_ID]
        fs = globals.gridfs.GridFS(globals.db,sensorId + "/data")
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
    fs = globals.gridfs.GridFS(globals.db,msg[globals.SENSOR_ID]+ "/data")
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

def getLocationMessage(msg):
    """
    get the location message corresponding to a data message.
    """
    return globals.db.locationMessages.find_one({globals.SENSOR_ID:msg[globals.SENSOR_ID], "t": {"$lte":msg["t"]}})

def getNextAcquisition(msg):
    """
    get the next acquisition for this message or None if none found.
    """
    query = {globals.SENSOR_ID: msg[globals.SENSOR_ID], "t":{"$gt": msg["t"]}, "freqRange":msg['freqRange']}
    return globals.db.dataMessages.find_one(query)

def getPrevAcquisition(msg):
    """
    get the prev acquisition for this message or None if none found.
    """
    query = {globals.SENSOR_ID: msg[globals.SENSOR_ID], "t":{"$lt": msg["t"]}, "freqRange":msg["freqRange"]}
    cur = globals.db.dataMessages.find(query)
    if cur == None or cur.count() == 0:
        return None
    sortedCur = cur.sort('t', pymongo.DESCENDING).limit(10)
    return sortedCur.next()

def getPrevDayBoundary(msg):
    """
    get the previous acquisition day boundary.
    """
    prevMsg = getPrevAcquisition(msg)
    if prevMsg == None:
        locationMessage = msgutils.getLocationMessage(msg)
        return  timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg['t'], locationMessage[globals.TIME_ZONE_KEY])
    locationMessage = msgutils.getLocationMessage(prevMsg)
    timeZone = locationMessage[globals.TIME_ZONE_KEY]
    return timezone.getDayBoundaryTimeStampFromUtcTimeStamp(prevMsg['t'], timeZone)

def getNextDayBoundary(msg):
    """
    get the next acquistion day boundary.
    """
    nextMsg = getNextAcquisition(msg)
    if nextMsg == None:
        locationMessage = msgutils.getLocationMessage(msg)
        return  timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg['t'], locationMessage[globals.TIME_ZONE_KEY])
    locationMessage = getLocationMessage(nextMsg)
    timeZone = locationMessage[globals.TIME_ZONE_KEY]
    nextDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(nextMsg['t'], timeZone)
    if globals.debug:
        thisDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg['t'], locationMessage[globals.TIME_ZONE_KEY])
        print "getNextDayBoundary: dayBoundary difference ", (nextDayBoundary - thisDayBoundary) / 60 / 60
    return nextDayBoundary


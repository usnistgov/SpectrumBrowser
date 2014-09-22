import numpy as np
import struct
import util
import flaskr as globals
from bson.objectid import ObjectId

# Message utilities.

def getCalData(systemMessage) :
    """
    Get the data associated with a system message.
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

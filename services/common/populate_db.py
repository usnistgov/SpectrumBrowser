import struct
import json
import pymongo
import numpy as np
import os
import gridfs
import argparse
import time
import timezone
import util
import sys
import authentication
import DbCollections
import SensorDb
import Message
import DataMessage
import LocationMessage
from Defines import SENSOR_ID, TIME_ZONE_KEY, SENSOR_KEY, FFT_POWER, SWEPT_FREQUENCY
from Defines import SYS
from Defines import DATA
from Defines import DATA_TYPE
from Defines import LOC
from Defines import CAL
from Defines import DATA_KEY
from Defines import TYPE

from Defines import LAT
from Defines import LON
from Defines import ALT
from Defines import NOISE_FLOOR
from Defines import ENABLED
from Defines import BINARY_FLOAT32, ASCII, BINARY_INT16, BINARY_INT8
from Defines import MEASUREMENT_TYPE
from Defines import SYS_TO_DETECT

# bulk = db.spectrumdb.initialize_ordered_bulk_op()
# bulk.find({}).remove()

timeStampBug = False


def roundTo2DecimalPlaces(value):
    newVal = int(value * 100)
    return float(newVal) / float(100)


def getDataTypeLength(dataType):
    if dataType == BINARY_FLOAT32:
        return 4
    elif dataType == BINARY_INT8:
        return 1
    else:
        return 1


# Read ascii from a file descriptor.
def readAsciiFromFile(fileDesc):
    csvValues = ""
    while True:
        char = fileDesc.read(1)
        if char == "[":
            csvValues += "["
            break
    while True:
        char = fileDesc.read(1)
        csvValues += char
        if char == "]":
            break
    return csvValues


def readDataFromFileDesc(fileDesc, dataType, count):
    if dataType != ASCII:
        dataTypeLength = getDataTypeLength(dataType)
        if fileDesc != None:
            dataBytes = fileDesc.read(dataTypeLength * count)
    else:
        dataBytes = readAsciiFromFile(fileDesc)
    return dataBytes


def put_data(jsonString,
             headerLength,
             filedesc=None,
             powers=None,
             streamOccupancies=None):
    """
    put data in the database. jsonString starts with {. If filedesc is None
    then the data part of the message is appended to the message (immediately follows it).
    Otherwise, the data is read from filedesc.
    """

    start_time = time.time()

    if filedesc == None:
        # We are not reading from a file:
        # Assume we are given the message in the string with the data
        # tacked at the end of it.
        jsonStringBytes = jsonString[0:headerLength]
    else:
        jsonStringBytes = jsonString

    util.debugPrint("jsonStringBytes = " + jsonStringBytes)
    jsonData = json.loads(jsonStringBytes)
    sensorId = jsonData[SENSOR_ID]
    sensorKey = jsonData[SENSOR_KEY]
    if not authentication.authenticateSensor(sensorId, sensorKey):
        raise Exception("Sensor Authentication Failure")

    sensorObj = SensorDb.getSensorObj(sensorId)
    if not sensorObj.getSensorStatus() == ENABLED:
        raise Exception("Sensor is disabled")

    # remove the sensor key from metadata for safety.
    del jsonData[SENSOR_KEY]

    locationPosts = DbCollections.getLocationMessages()
    systemPosts = DbCollections.getSystemMessages()
    dataPosts = DbCollections.getDataMessages(sensorId)
    db = DbCollections.getSpectrumDb()
    currentLocalTime = time.time()
    Message.setInsertionTime(jsonData, currentLocalTime)
    if jsonData[TYPE] == SYS:
        # see if this system message already exists in the DB to avoid duplicates.
        query = {SENSOR_ID: jsonData[SENSOR_ID], "t": jsonData["t"]}
        found = systemPosts.find_one(query)
        if CAL in jsonData:
            calStr = jsonData[CAL]
            # Ugly!! Need to fix this.
            if calStr != "N/A":
                n = jsonData[CAL]["mPar"]["n"]
                nM = jsonData[CAL]["nM"]
                sensorId = jsonData[SENSOR_ID]
                if n * nM != 0:
                    dataType = jsonData[CAL][DATA_TYPE]
                    lengthToRead = n * nM
                    if filedesc != None:
                        messageBytes = readDataFromFileDesc(filedesc, dataType,
                                                            lengthToRead)
                    elif powers == None:
                        messageBytes = jsonString[headerLength:]
                    else:
                        # TODO -- deal with the other data types here
                        messageBytes = struct.pack('%sb' % len(powers), *
                                                   powers)
                fs = gridfs.GridFS(db, jsonData[SENSOR_ID] + "_data")
                key = fs.put(messageBytes)
                jsonData[CAL][DATA_KEY] = str(key)

        if found == None:
            systemPosts.ensure_index([('t', pymongo.DESCENDING)])
            systemPosts.insert(jsonData)
        else:
            util.debugPrint("not inserting duplicate system post")
        end_time = time.time()
        util.debugPrint("Insertion time " + str(end_time - start_time))
    elif jsonData[TYPE] == LOC:
        print(json.dumps(jsonData, sort_keys=True, indent=4))
        sensorId = jsonData[SENSOR_ID]
        t = jsonData['t']
        lat = jsonData[LAT]
        lon = jsonData[LON]
        alt = jsonData[ALT]
        query = {SENSOR_ID: sensorId, LAT: lat, LON: lon, ALT: alt}
        locMsg = locationPosts.find_one(query)
        if locMsg != None:
            print "Location Post already exists - not updating "
            return
        (to_zone, timeZoneName) = timezone.getLocalTimeZoneFromGoogle(t, lat,
                                                                      lon)
        # If google returned null, then override with local information
        if to_zone == None:
            if TIME_ZONE_KEY in jsonData:
                to_zone = jsonData[TIME_ZONE_KEY]
            else:
                print "ERROR: Unable to determine timeZone"
                return
        else:
            jsonData[TIME_ZONE_KEY] = to_zone
        # insert the loc message into the database.
        db.locationMessages.ensure_index([('t', pymongo.DESCENDING)])
        locationPosts.insert(jsonData)
        end_time = time.time()
        print "inserted Location Message. Insertion time " + str(end_time -
                                                                 start_time)
    elif jsonData[TYPE] == DATA:
        # BUG BUG -- we need to fix this. Need new data.
        if not SYS_TO_DETECT in jsonData:
            jsonData[SYS_TO_DETECT] = "LTE"
        # Fix up issue with sys2detect - should have no spaces. 
        # BUGBUG -- this is ugly. Should reject the data.
        jsonData[SYS_TO_DETECT] = jsonData[SYS_TO_DETECT].replace(" ", "")
        DataMessage.init(jsonData)

        freqRange = DataMessage.getFreqRange(jsonData)

        lastSystemPost = systemPosts.find_one(
            {SENSOR_ID: sensorId,
             "t": {"$lte": Message.getTime(jsonData)}})
        lastLocationPost = locationPosts.find_one(
            {SENSOR_ID: sensorId,
             "t": {"$lte": Message.getTime(jsonData)}})
        if lastLocationPost == None or lastSystemPost == None:
            raise Exception("Location post or system post not found for " +
                            sensorId)
        # Check for duplicates
        query = {SENSOR_ID: sensorId, "t": Message.getTime(jsonData)}
        found = DbCollections.getDataMessages(sensorId).find_one(query)
        # record the location message associated with the data.
        DataMessage.setLocationMessageId(jsonData,
                                         str(lastLocationPost['_id']))
        DataMessage.setSystemMessageId(jsonData, str(lastSystemPost['_id']))
        # prev data message.
        lastSeenDataMessageSeqno = db.lastSeenDataMessageSeqno.find_one(
            {SENSOR_ID: sensorId})
        # update the seqno
        if lastSeenDataMessageSeqno == None:
            seqNo = 1
            db.lastSeenDataMessageSeqno.insert({SENSOR_ID: sensorId,
                                                "seqNo": seqNo})
        else:
            seqNo = lastSeenDataMessageSeqno["seqNo"] + 1
            lastSeenDataMessageSeqno["seqNo"] = seqNo
            db.lastSeenDataMessageSeqno.update(
                {"_id": lastSeenDataMessageSeqno["_id"]},
                {"$set": lastSeenDataMessageSeqno},
                upsert=False)
        jsonData["seqNo"] = seqNo
        nM = DataMessage.getNumberOfMeasurements(jsonData)
        n = DataMessage.getNumberOfFrequencyBins(jsonData)
        lengthToRead = n * nM
        dataType = DataMessage.getDataType(jsonData)
        if lengthToRead != 0:
            if filedesc != None:
                messageBytes = readDataFromFileDesc(filedesc, dataType,
                                                    lengthToRead)
            elif powers == None:
                messageBytes = jsonString[headerLength:]
            else:
                # TODO - deal with the other data types here.
                messageBytes = struct.pack("%sb" % len(powers), *powers)

        occupancyBytes = None
        if streamOccupancies != None:
            occupancyBytes = struct.pack("%sb" % len(streamOccupancies), *
                                         streamOccupancies)

            # Note: The data needs to be read before it is rejected.
        if found != None:
            util.debugPrint("ignoring duplicate data message")
            return

        if lengthToRead != 0:
            fs = gridfs.GridFS(db, sensorId + "_data")
            key = fs.put(messageBytes)
            DataMessage.setDataKey(jsonData, str(key))

        if occupancyBytes != None:
            key = fs.put(occupancyBytes)
            DataMessage.setOccupancyKey(jsonData, str(key))
            DataMessage.setOccupancyVectorLength(jsonData, len(occupancyBytes))

        cutoff = DataMessage.getThreshold(jsonData)
        sensorMeasurementType = SensorDb.getSensor(sensorId)[MEASUREMENT_TYPE]
        if DataMessage.getMeasurementType(jsonData) != sensorMeasurementType:
            raise Exception(
                "MeasurementType Mismatch between sensor and DataMessage")

        dataPosts.ensure_index([('t', pymongo.ASCENDING)])
        maxPower = -1000
        minPower = 1000
        if DataMessage.getMeasurementType(jsonData) == FFT_POWER:
            occupancyCount = [0 for i in range(0, nM)]
            if powers == None:
                powerVal = np.array(np.zeros(n * nM))
            else:
                powerVal = np.array(powers)
            # unpack the power array.
            if dataType == BINARY_INT8 and powers == None:
                for i in range(0, lengthToRead):
                    powerVal[i] = struct.unpack('b', messageBytes[i:i + 1])[0]
            maxPower = np.max(powerVal)
            minPower = np.min(powerVal)
            powerArray = powerVal.reshape(nM, n)
            for i in range(0, nM):
                occupancyCount[i] = float(len(filter(
                    lambda x: x >= cutoff, powerArray[i, :]))) / float(n)
            DataMessage.setMaxOccupancy(jsonData,
                                        float(np.max(occupancyCount)))
            DataMessage.setMeanOccupancy(jsonData,
                                         float(np.mean(occupancyCount)))
            DataMessage.setMinOccupancy(jsonData,
                                        float(np.min(occupancyCount)))
            DataMessage.setMedianOccupancy(jsonData,
                                           float(np.median(occupancyCount)))
        else:
            if dataType == ASCII:
                powerVal = eval(messageBytes)
            else:
                for i in range(0, lengthToRead):
                    powerVal[i] = struct.unpack('f', messageBytes[i:i + 4])[0]
            maxPower = np.max(powerVal)
            minPower = np.min(powerVal)
            occupancyCount = float(len(filter(lambda x: x >= cutoff,
                                              powerVal)))
            DataMessage.setOccupancy(jsonData, occupancyCount /
                                     float(len(powerVal)))
        DataMessage.setMaxPower(jsonData, maxPower)
        DataMessage.setMinPower(jsonData, minPower)
        #if filedesc != None:
        #    print json.dumps(jsonData, sort_keys=True, indent=4)
        dataPosts.insert(jsonData)
        if not "sensorFreq" in lastLocationPost:
            lastLocationPost['sensorFreq'] = [freqRange]
        else:
            freqRanges = lastLocationPost['sensorFreq']
            if not freqRange in freqRanges:
                freqRanges.append(freqRange)
            lastLocationPost['sensorFreq'] = freqRanges
        # if we have not registered the first data message in the location post, update it.
        if not 'firstDataMessageTimeStamp' in lastLocationPost:
            LocationMessage.setFirstDataMessageTimeStamp(
                lastLocationPost, Message.getTime(jsonData))
            LocationMessage.setLastDataMessageTimeStamp(
                lastLocationPost, Message.getTime(jsonData))
        else:
            LocationMessage.setLastDataMessageTimeStamp(
                lastLocationPost, Message.getTime(jsonData))
        if not 'minPower' in lastLocationPost:
            lastLocationPost["minPower"] = minPower
            lastLocationPost["maxPower"] = maxPower
        else:
            lastLocationPost["minPower"] = np.minimum(
                lastLocationPost["minPower"], minPower)
            lastLocationPost["maxPower"] = np.maximum(
                lastLocationPost["maxPower"], maxPower)
        if not "maxOccupancy" in lastLocationPost:
            if jsonData["mType"] == SWEPT_FREQUENCY:
                lastLocationPost["maxOccupancy"] = jsonData["occupancy"]
                lastLocationPost["minOccupancy"] = jsonData["occupancy"]
            else:
                lastLocationPost["maxOccupancy"] = jsonData["maxOccupancy"]
                lastLocationPost["minOccupancy"] = jsonData["minOccupancy"]
        else:
            if DataMessage.getMeasurementType(jsonData) == SWEPT_FREQUENCY:
                lastLocationPost["maxOccupancy"] = np.maximum(
                    lastLocationPost["maxOccupancy"], jsonData["occupancy"])
                lastLocationPost["minOccupancy"] = np.minimum(
                    lastLocationPost["minOccupancy"], jsonData["occupancy"])
            else:
                lastLocationPost["maxOccupancy"] = np.maximum(
                    lastLocationPost["maxOccupancy"], jsonData["maxOccupancy"])
                lastLocationPost["minOccupancy"] = np.minimum(
                    lastLocationPost["minOccupancy"], jsonData["minOccupancy"])

        locationPosts.update({"_id": lastLocationPost["_id"]},
                             {"$set": lastLocationPost},
                             upsert=False)
        end_time = time.time()
        if filedesc != None:
            print "Data Message: seqNo: " + str(
                seqNo) + " Insertion time " + str(end_time - start_time)


def put_data_from_file(filename):
    """
    Read data from a file and put it into the database.
    """
    f = open(filename)
    while True:
        headerLengthStr = ""
        while True:
            c = f.read(1)
            if c == "":
                print "Done reading file"
                return
            if c == '\r':
                if headerLengthStr != "":
                    break
            elif c == '\n':
                if headerLengthStr != "":
                    break
            else:
                headerLengthStr = headerLengthStr + c
        print "headerLengthStr = ", headerLengthStr
        jsonHeaderLength = int(headerLengthStr.rstrip())
        jsonStringBytes = f.read(jsonHeaderLength)
        put_data(jsonStringBytes, jsonHeaderLength, filedesc=f)


def putDataFromFile(filename):
    f = open(filename)
    while True:
        jsonHeaderLengthStr = f.read(4)
        if jsonHeaderLengthStr == "":
            print "End of stream"
            break
        jsonHeaderLength = struct.unpack('i', jsonHeaderLengthStr[0:4])[0]
        jsonStringBytes = f.read(jsonHeaderLength)
        put_data(jsonStringBytes, jsonHeaderLength, filedesc=f)


def put_message(message):
    """
    Read data from a message string
    """
    index = message.index("{")
    lengthString = message[0:index - 1].rstrip()
    messageLength = int(lengthString)
    print messageLength
    put_data(message[index:], messageLength)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument('-data', help='Filename with readings')
    args = parser.parse_args()
    filename = args.data
    put_data_from_file(filename)

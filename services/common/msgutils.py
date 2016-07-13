# -*- coding: utf-8 -*-
#
#This software was developed by employees of the National Institute of
#Standards and Technology (NIST), and others.
#This software has been contributed to the public domain.
#Pursuant to title 15 Untied States Code Section 105, works of NIST
#employees are not subject to copyright protection in the United States
#and are considered to be in the public domain.
#As a result, a formal license is not needed to use this software.
#
#This software is provided "AS IS."
#NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
#OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
#MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
#AND DATA ACCURACY.  NIST does not warrant or make any representations
#regarding the use of the software or the results thereof, including but
#not limited to the correctness, accuracy, reliability or usefulness of
#this software.

import numpy as np
import struct
import util
import msgutils
import pymongo
import timezone
from bson.objectid import ObjectId
import gridfs
import DbCollections
import Defines
from Defines import SENSOR_ID, TIME_ZONE_KEY, \
    DATA_TYPE, FREQ_RANGE, OCCUPANCY_KEY, OCCUPANCY_VECTOR_LENGTH
import DebugFlags
from Defines import ASCII, BINARY_INT8, BINARY_FLOAT32, BINARY_INT16
import DataMessage


# Message utilities.
def freqRange(sys2detect, fmin, fmax):
    sd = sys2detect.replace(" ", "").replace(":", "")
    return sd + ":" + str(int(fmin)) + ":" + str(int(fmax))


def getMaxMinFreq(msg):
    """
    Get the max and min frequencies from a message.
    """
    return (msg["mPar"]["fStop"], msg["mPar"]["fStart"])


def getCalData(systemMessage):
    """
    Get the data associated with a Cal message.
    """
    if not Defines.CAL in systemMessage:
        return None
    msg = systemMessage[Defines.CAL]
    if msg != "N/A":
        sensorId = systemMessage[SENSOR_ID]
        fs = gridfs.GridFS(DbCollections.getSpectrumDb(), sensorId + "_data")
        messageBytes = fs.get(ObjectId(msg[Defines.DATA_KEY])).read()
        nM = msg["nM"]
        n = msg["mPar"]["n"]
        lengthToRead = nM * n
        if lengthToRead is None:
            util.debugPrint("No data to read")
            return None
        if msg[DATA_TYPE] == ASCII:
            powerVal = eval(messageBytes)
        elif msg[DATA_TYPE] == BINARY_INT8:
            powerVal = np.array(np.zeros(n * nM))
            for i in range(0, lengthToRead):
                powerVal[i] = float(struct.unpack('b', messageBytes[i:i + 1])[
                    0])
        elif msg[DATA_TYPE] == BINARY_INT16:
            powerVal = np.array(np.zeros(n * nM))
            for i in range(0, lengthToRead, 2):
                powerVal[i] = float(struct.unpack('h', messageBytes[i:i + 2])[
                    0])
        elif msg[DATA_TYPE] == BINARY_FLOAT32:
            powerVal = np.array(np.zeros(n * nM))
            for i in range(0, lengthToRead, 4):
                powerVal[i] = float(struct.unpack('f', messageBytes[i:i + 4])[
                    0])
        return powerVal
    else:
        return None


# Extract data from a data message
def getData(msg):
    """
    get the data associated with a data message.
    """
    fs = gridfs.GridFS(DbCollections.getSpectrumDb(), msg[SENSOR_ID] + "_data")
    messageBytes = fs.get(ObjectId(msg[Defines.DATA_KEY])).read()
    nM = int(msg["nM"])
    n = int(msg["mPar"]["n"])
    lengthToRead = nM * n  #int(nM * n)
    if lengthToRead == 0:
        util.debugPrint("No data to read")
        return None
    if msg[DATA_TYPE] == ASCII:
        powerVal = eval(messageBytes)
    elif msg[DATA_TYPE] == BINARY_INT8:
        powerVal = np.array(np.zeros(n * nM))
        for i in range(0, int(lengthToRead)):
            powerVal[i] = float(struct.unpack('b', messageBytes[i:i + 1])[0])
    elif msg[DATA_TYPE] == BINARY_INT16:
        powerVal = np.array(np.zeros(n * nM))
        for i in range(0, lengthToRead, 2):
            powerVal[i] = float(struct.unpack('h', messageBytes[i:i + 2])[0])
    elif msg[DATA_TYPE] == BINARY_FLOAT32:
        powerVal = np.array(np.zeros(n * nM))
        for i in range(0, lengthToRead, 4):
            powerVal[i] = float(struct.unpack('f', messageBytes[i:i + 4])[0])
    return list(powerVal)


def getOccupancyData(msg):
    """
    get the occupancy data associated with a message if any.
    """

    messageBytes = getData(msg)
    powerArray = np.array(messageBytes)
    cutoff = DataMessage.getThreshold(msg)
    nM = DataMessage.getNumberOfMeasurements(msg)
    n = DataMessage.getNumberOfFrequencyBins(msg)
    occupancyVal = np.array(np.zeros(nM))
    powerArray = powerArray.reshape(nM, n)
    for i in range(0, nM):
        occupancyVal[i] = len(filter(lambda x: x >= cutoff, powerArray[i,:]))

    return occupancyVal


def getDataAsArray(msg):
    """
    get the data associated with the message as an Nmxn array.
    """

    messageBytes = getData(msg)
    powerArray = np.array(messageBytes)
    nM = DataMessage.getNumberOfMeasurements(msg)
    n = DataMessage.getNumberOfFrequencyBins(msg)
    return powerArray.reshape(nM, n)


def removeData(msg):
    if Defines.DATA_KEY in msg:
        fs = gridfs.GridFS(DbCollections.getSpectrumDb(),
                           msg[SENSOR_ID] + "_data")
        fileId = fs.get(ObjectId(msg[Defines.DATA_KEY]))
        fs.delete(ObjectId(msg[Defines.DATA_KEY]))


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
    tzId = msg[TIME_ZONE_KEY]
    return timezone.getDayBoundaryTimeStampFromUtcTimeStamp(timeStamp, tzId)


def getLocationMessage(msg):
    """
    get the location message corresponding to a data message.
    """
    return DbCollections.getLocationMessages().find_one(
        {SENSOR_ID: msg[SENSOR_ID],
         "t": {"$lte": msg["t"]}})


def getNextAcquisition(msg):
    """
    get the next acquisition for this message or None if none found.
    """
    query = {SENSOR_ID: msg[SENSOR_ID],
             "t": {"$gt": msg["t"]},
             FREQ_RANGE: msg[FREQ_RANGE]}
    return DbCollections.getDataMessages(msg[SENSOR_ID]).find_one(query)


def getPrevAcquisition(msg):
    """
    get the prev acquisition for this message or None if none found.
    """
    query = {SENSOR_ID: msg[SENSOR_ID],
             "t": {"$lt": msg["t"]},
             FREQ_RANGE: msg[FREQ_RANGE]}
    cur = DbCollections.getDataMessages(msg[SENSOR_ID]).find(query)
    if cur is None or cur.count() == 0:
        return None
    sortedCur = cur.sort('t', pymongo.DESCENDING).limit(10)
    return sortedCur.next()


def getLastAcquisition(sensorId, sys2detect, minFreq, maxFreq):
    """
    get the last acquisiton of the collection.
    """
    query = {SENSOR_ID: sensorId,
             FREQ_RANGE: freqRange(sys2detect, minFreq, maxFreq)}
    util.debugPrint(query)
    cur = DbCollections.getDataMessages(sensorId).find(query)
    if cur is None or cur.count() == 0:
        return None
    sortedCur = cur.sort('t', pymongo.DESCENDING).limit(10)
    return sortedCur.next()


def getLastAcquisitonTimeStamp(sensorId, sys2detect, minFreq, maxFreq):
    """
    get the time of the last aquisition of the collection.
    """
    msg = getLastAcquisition(sensorId, sys2detect, minFreq, maxFreq)
    if msg is None:
        return -1
    else:
        return msg['t']


def getLastSensorAcquisitionTimeStamp(sensorId):
    """
    get the last capture from the sensor, given its ID.
    """
    cur = DbCollections.getDataMessages(sensorId).find({SENSOR_ID: sensorId})
    if cur is None or cur.count() == 0:
        return -1
    else:
        sortedCur = cur.sort('t', pymongo.DESCENDING).limit(10)
        lastDataMessage = sortedCur.next()
        return lastDataMessage["t"]


def getLastSensorAcquisition(sensorId):
    cur = DbCollections.getLocationMessages(sensorId).find(
        {SENSOR_ID: sensorId})
    if cur is None or cur.count() == 0:
        return None
    else:
        sortedCur = cur.sort('t', pymongo.DESCENDING).limit(10)
        locationMessage = sortedCur.next()
        return DbCollections.getDataMessages(sensorId).find_one(
            {"t": locationMessage["lastDataMessageTimeStamp"],
             SENSOR_ID: sensorId})


def getCaptureEventTimes(sensorId):
    """
    get an ordered list of all capture events from the sensor, most recent event first.

    at present the capture event feature is not implemented.  An ordered list of data
    message timestamps for this sensor is returned instead
    """
    cur = DbCollections.getDataMessages(sensorId).find({SENSOR_ID: sensorId})
    if cur is None or cur.count() == 0:
        return -1
    else:
        captureEventTimes = []
        for dataMsg in cur.sort('t', pymongo.DESCENDING):
            eventTime = timezone.getDateTimeFromLocalTimeStamp(dataMsg["t"])
            captureEventTimes.append(eventTime)
        return captureEventTimes


def getPrevDayBoundary(msg):
    """
    get the previous acquisition day boundary.
    """
    prevMsg = getPrevAcquisition(msg)
    if prevMsg is None:
        locationMessage = getLocationMessage(msg)
        return timezone.getDayBoundaryTimeStampFromUtcTimeStamp(
            msg['t'], locationMessage[TIME_ZONE_KEY])
    locationMessage = msgutils.getLocationMessage(prevMsg)
    timeZone = locationMessage[TIME_ZONE_KEY]
    return timezone.getDayBoundaryTimeStampFromUtcTimeStamp(prevMsg['t'],
                                                            timeZone)


def getDayBoundaryTimeStamp(msg):
    """
    Get the universal time stamp for the day boundary of this message.
    """
    locationMessage = getLocationMessage(msg)
    timeZone = locationMessage[TIME_ZONE_KEY]
    return timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg['t'], timeZone)


def getNextDayBoundary(msg):
    """
    get the next acquistion day boundary.
    """
    nextMsg = getNextAcquisition(msg)
    if nextMsg is None:
        locationMessage = getLocationMessage(msg)
        return timezone.getDayBoundaryTimeStampFromUtcTimeStamp(
            msg['t'], locationMessage[TIME_ZONE_KEY])
    locationMessage = getLocationMessage(nextMsg)
    timeZone = locationMessage[TIME_ZONE_KEY]
    nextDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(
        nextMsg['t'], timeZone)
    if DebugFlags.debug:
        thisDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(
            msg['t'], locationMessage[TIME_ZONE_KEY])
        util.debugPrint("getNextDayBoundary: dayBoundary difference " + str((
            nextDayBoundary - thisDayBoundary) / 60 / 60))
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
    powerArray = np.array(
        [data[i] for i in range(topReadingsToIgnore, n - endReadingsToIgnore)])
    return powerArray


def trimNoiseFloorToSubBand(msg, subBandMinFreq, subBandMaxFreq):
    """
    Trim noise floor to a sub band of a measurement band.
    """
    data = msg['wnI']
    n = msg["mPar"]["n"]
    minFreq = msg["mPar"]["fStart"]
    maxFreq = msg["mPar"]["fStop"]
    freqRangePerReading = float(maxFreq - minFreq) / float(n)
    endReadingsToIgnore = int((maxFreq - subBandMaxFreq) / freqRangePerReading)
    topReadingsToIgnore = int((subBandMinFreq - minFreq) / freqRangePerReading)
    powerArray = np.array(
        [data[i] for i in range(topReadingsToIgnore, n - endReadingsToIgnore)])
    return powerArray

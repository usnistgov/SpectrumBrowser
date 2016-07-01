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


import util
import timezone
import msgutils
from Defines import SECONDS_PER_DAY, TIME_ZONE_KEY, SENSOR_ID, FREQ_RANGE, STATUS, ERROR_MESSAGE, OK, NOK
from Defines import CHANNEL_COUNT
from Defines import ACQUISITION_COUNT
from Defines import TIME
from Defines import SECONDS_PER_HOUR
import DbCollections
import DataMessage
import LocationMessage
import SensorDb
import numpy as np


def compute_stats_for_fft_power(cursor):
    util.debugPrint("compute_daily_max_min_mean_stats_for_fft_power")
    meanOccupancy = 0
    minOccupancy = 10000
    maxOccupancy = -1
    nReadings = cursor.count()
    util.debugPrint("nreadings = " + str(nReadings))
    if nReadings == 0:
        util.debugPrint("zero count")
        return None
    dayBoundaryTimeStamp = None
    count = cursor.count()
    for msg in cursor:
        if dayBoundaryTimeStamp == None:
            dayBoundaryTimeStamp = msgutils.getDayBoundaryTimeStamp(msg)
        n = msg["mPar"]["n"]
        minFreq = msg["mPar"]["fStart"]
        maxFreq = msg["mPar"]["fStop"]
        cutoff = msg["cutoff"]
        maxOccupancy = np.maximum(maxOccupancy, msg["maxOccupancy"])
        minOccupancy = np.minimum(minOccupancy, msg["minOccupancy"])
        meanOccupancy = meanOccupancy + msg["meanOccupancy"]
    meanOccupancy = float(meanOccupancy) / float(nReadings)
    return (n, maxFreq, minFreq, cutoff, \
         {"count": count, \
         "dayBoundaryTimeStamp" : dayBoundaryTimeStamp, \
         "maxOccupancy":maxOccupancy, \
         "minOccupancy":minOccupancy, \
         "meanOccupancy":meanOccupancy})


def getOneDayStats(sensorId, startTime, sys2detect, minFreq, maxFreq):
    """
    Generate and return a JSON structure with the one day statistics.

    startTime is the start time in UTC
    sys2detect is the system to detect.
    minFreq is the minimum frequency of the frequency band of interest.
    maxFreq is the maximum frequency of the frequency band of interest.

    """
    freqRange = msgutils.freqRange(sys2detect, minFreq, maxFreq)
    mintime = int(startTime)
    maxtime = mintime + SECONDS_PER_DAY
    query = {SENSOR_ID: sensorId,
             "t": {"$lte": maxtime,
                   "$gte": mintime},
             FREQ_RANGE: freqRange}
    util.debugPrint(query)
    msg = DbCollections.getDataMessages(sensorId).find_one(query)
    if msg == None:
        return {STATUS: NOK, ERROR_MESSAGE: "Data message not found"}
    locationMessage = msgutils.getLocationMessage(msg)
    tzId = locationMessage[TIME_ZONE_KEY]
    mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg["t"], tzId)
    maxtime = mintime + SECONDS_PER_DAY
    query = {SENSOR_ID: sensorId,
             "t": {"$lte": maxtime,
                   "$gte": mintime},
             FREQ_RANGE: freqRange}
    cur = DbCollections.getDataMessages(sensorId).find(query)
    if cur == None:
        return {STATUS: NOK, ERROR_MESSAGE: "Data messages not found"}
    res = {}
    values = {}
    res["formattedDate"] = timezone.formatTimeStampLong(
        mintime, locationMessage[TIME_ZONE_KEY])
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
                        "maxOccupancy":msg["maxOccupancy"], \
                        "minOccupancy":msg["minOccupancy"], \
                        "meanOccupancy":msg["meanOccupancy"], \
                        "medianOccupancy":msg["medianOccupancy"]}
    query = {SENSOR_ID: sensorId, "t": {"$gt": maxtime}, FREQ_RANGE: freqRange}
    msg = DbCollections.getDataMessages(sensorId).find_one(query)
    if msg != None:
        nextDay = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg["t"],
                                                                   tzId)
    else:
        nextDay = mintime
    if prevMsg != None:
        prevDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(
            prevMsg["t"], tzId)
        query = {SENSOR_ID: sensorId,
                 "t": {"$gte": prevDayBoundary},
                 FREQ_RANGE: freqRange}
        msg = DbCollections.getDataMessages(sensorId).find_one(query)
        prevDay = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg["t"],
                                                                   tzId)
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

def getHourlyMaxMinMeanStats(sensorId, startTime, sys2detect, fmin, \
                             fmax, subBandMinFreq, subBandMaxFreq, sessionId):

    sensor = SensorDb.getSensor(sensorId)
    if sensor == None:
        return {STATUS: NOK, ERROR_MESSAGE: "Sensor Not Found"}

    tstart = int(startTime)
    fmin = int(subBandMinFreq)
    fmax = int(subBandMaxFreq)
    freqRange = msgutils.freqRange(sys2detect, fmin, fmax)

    queryString = { SENSOR_ID : sensorId, TIME : {'$gte':tstart}, \
                   FREQ_RANGE: freqRange}
    util.debugPrint(queryString)
    startMessage = DbCollections.getDataMessages(sensorId).find_one(
        queryString)
    if startMessage == None:
        errorStr = "Start Message Not Found"
        util.debugPrint(errorStr)
        response = {STATUS: NOK, ERROR_MESSAGE: "No data found"}
        return response

    locationMessageId = DataMessage.getLocationMessageId(startMessage)

    retval = {STATUS: OK}

    values = {}

    locationMessage = DbCollections.getLocationMessages().find_one(
        {"_id": locationMessageId})

    tZId = LocationMessage.getTimeZone(locationMessage)

    tmin = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(
        tstart, LocationMessage.getTimeZone(locationMessage))

    for hour in range(0, 23):
        dataMessages = DbCollections.getDataMessages(sensorId).find({"t":{"$gte":tmin + hour * SECONDS_PER_HOUR}, \
                                                                      "t" :{"$lte":(hour + 1) * SECONDS_PER_HOUR}, \
                                                                      FREQ_RANGE:freqRange})
        if dataMessages != None:
            stats = compute_stats_for_fft_power(dataMessages)
            (nChannels, maxFreq, minFreq, cutoff, result) = stats
            values[hour] = result

    retval["values"] = values

    # Now compute the next interval after the last one (if one exists)
    tend = tmin + SECONDS_PER_DAY
    queryString = {SENSOR_ID: sensorId,
                   TIME: {'$gte': tend},
                   FREQ_RANGE: freqRange}
    msg = DbCollections.getDataMessages(sensorId).find_one(queryString)
    if msg == None:
        result["nextTmin"] = tmin
    else:
        nextTmin = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg[TIME],
                                                                    tZId)
        result["nextTmin"] = nextTmin
    # Now compute the previous interval before this one.
    prevMessage = msgutils.getPrevAcquisition(startMessage)
    if prevMessage != None:
        newTmin = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(
            prevMessage[TIME] - SECONDS_PER_DAY, tZId)
        queryString = { SENSOR_ID : sensorId, TIME : {'$gte':newTmin}, \
                       FREQ_RANGE:msgutils.freqRange(sys2detect, fmin, fmax)}
        msg = DbCollections.getDataMessages(sensorId).find_one(queryString)
    else:
        msg = startMessage
    result[STATUS] = OK
    result["prevTmin"] = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(
        msg[TIME], tZId)
    result["tmin"] = tmin
    result["maxFreq"] = maxFreq
    result["minFreq"] = minFreq
    result["cutoff"] = cutoff
    result[CHANNEL_COUNT] = nChannels
    result["startDate"] = timezone.formatTimeStampLong(tmin, tZId)
    result["values"] = values

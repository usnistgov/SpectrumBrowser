# -*- coding: utf-8 -*-
#
# This software was developed by employees of the National Institute of
# Standards and Technology (NIST), and others.
# This software has been contributed to the public domain.
# Pursuant to title 15 Untied States Code Section 105, works of NIST
# employees are not subject to copyright protection in the United States
# and are considered to be in the public domain.
# As a result, a formal license is not needed to use this software.
#
# This software is provided "AS IS."
# NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
# OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
# AND DATA ACCURACY.  NIST does not warrant or make any representations
# regarding the use of the software or the results thereof, including but
# not limited to the correctness, accuracy, reliability or usefulness of
# this software.

import timezone
import util
import pymongo
import msgutils
from Defines import TIME_ZONE_KEY, SENSOR_ID, SECONDS_PER_DAY, \
    FREQ_RANGE, THRESHOLDS, SYSTEM_TO_DETECT, \
    COUNT, MIN_FREQ_HZ, MAX_FREQ_HZ, BAND_STATISTICS, STATUS, TIME, UNKNOWN, \
    ERROR_MESSAGE, NOK, MEASUREMENT_TYPE, ACTIVE, LOCATION_MESSAGE_ID, \
    LON, LAT, ALT
import DbCollections
import SensorDb
import LocationMessage


def getSensorDataSummary(sensorId, locationMessage):
    sensor = SensorDb.getSensorObj(sensorId)
    if sensor is None:
        return {STATUS: NOK, ERROR_MESSAGE: "Sensor Not found"}
    measurementType = sensor.getMeasurementType()
    tzId = locationMessage[TIME_ZONE_KEY]
    acquisitionCount = LocationMessage.getMessageCount(locationMessage)
    util.debugPrint("AquistionCount " + str(acquisitionCount))
    if acquisitionCount == 0:
        return {"status": "OK",
                "minOccupancy": 0,
                "tStartReadings": 0,
                "tStartLocalTime": 0,
                "tStartLocalTimeFormattedTimeStamp": "UNKNOWN",
                "tStartDayBoundary": 0,
                "tEndDayBoundary": 0,
                "tEndReadings": 0,
                "tEndLocalTimeFormattedTimeStamp": "UNKNOWN",
                "maxOccupancy": 0,
                "measurementType": measurementType,
                "isStreamingEnabled": sensor.isStreamingEnabled(),
                "sensorStatus": sensor.getSensorStatus(),
                COUNT: 0}

    minTime = LocationMessage.getFirstDataMessageTimeStamp(locationMessage)
    maxTime = LocationMessage.getLastDataMessageTimeStamp(locationMessage)

    tStartDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(
        minTime, tzId)
    (minLocalTime, tStartLocalTimeTzName) = timezone.getLocalTime(minTime,
                                                                  tzId)

    tEndDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(maxTime,
                                                                       tzId)

    tstampMin = timezone.formatTimeStampLong(minTime, tzId)
    tstampMax = timezone.formatTimeStampLong(maxTime, tzId)
    retval = {"status": "OK",
              "maxOccupancy": 0,
              "minOccupancy": 0,
              "tStartReadings": minTime,
              "tStartLocalTime": minLocalTime,
              "tStartLocalTimeFormattedTimeStamp": tstampMin,
              "tStartDayBoundary": tStartDayBoundary,
              "tEndDayBoundary": tEndDayBoundary,
              "tEndReadings": maxTime,
              "tEndLocalTimeFormattedTimeStamp": tstampMax,
              "measurementType": measurementType,
              "isStreamingEnabled": sensor.isStreamingEnabled(),
              "sensorStatus": sensor.getSensorStatus(),
              COUNT: acquisitionCount}

    return retval


def getBandDataSummary(sensorId,
                       locationMessage,
                       sys2detect,
                       minFreq,
                       maxFreq,
                       mintime,
                       dayCount=None):
    sensor = SensorDb.getSensorObj(sensorId)

    if sensor is None:
        return {STATUS: NOK, ERROR_MESSAGE: "Sensor Not found"}
    measurementType = sensor.getMeasurementType()

    tzId = locationMessage[TIME_ZONE_KEY]
    locationMessageId = str(locationMessage["_id"])

    freqRange = msgutils.freqRange(sys2detect, minFreq, maxFreq)
    count = LocationMessage.getBandCount(locationMessage, freqRange)
    if count == 0:
        return {FREQ_RANGE: freqRange,
                COUNT: 0,
                "minFreq": minFreq,
                "maxFreq": maxFreq,
                SYSTEM_TO_DETECT: sys2detect}
    else:
        minOccupancy = LocationMessage.getMinBandOccupancy(locationMessage,
                                                           freqRange)
        maxOccupancy = LocationMessage.getMaxBandOccupancy(locationMessage,
                                                           freqRange)
        count = LocationMessage.getBandCount(locationMessage, freqRange)
        meanOccupancy = LocationMessage.getMeanOccupancy(locationMessage,
                                                         freqRange)
        minTime = LocationMessage.getFirstMessageTimeStampForBand(
            locationMessage, freqRange)
        maxTime = LocationMessage.getLastMessageTimeStampForBand(
            locationMessage, freqRange)

        maxTimes = timezone.getLocalTime(maxTime, tzId)
        (tEndReadingsLocalTime, tEndReadingsLocalTimeTzName) = maxTimes

        tEndDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(
            maxTime, tzId)
        tStartDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(
            minTime, tzId)

        tstampMin = timezone.formatTimeStampLong(minTime, tzId)
        tstampMax = timezone.formatTimeStampLong(maxTime, tzId)
        retval = {"tStartDayBoundary": tStartDayBoundary,
                  "tEndDayBoundary": tEndDayBoundary,
                  "tStartReadings": minTime,
                  "tStartLocalTime": minTime,
                  "tStartLocalTimeFormattedTimeStamp": tstampMin,
                  "tEndReadings": maxTime,
                  "tEndReadingsLocalTime": maxTime,
                  "tEndLocalTimeFormattedTimeStamp": tstampMax,
                  "tEndDayBoundary": tEndDayBoundary,
                  "maxOccupancy": maxOccupancy,
                  "meanOccupancy": meanOccupancy,
                  "minOccupancy": minOccupancy,
                  "maxFreq": maxFreq,
                  "minFreq": minFreq,
                  SYSTEM_TO_DETECT: sys2detect,
                  FREQ_RANGE: freqRange,
                  "measurementType": measurementType,
                  "active": sensor.isBandActive(sys2detect, minFreq, maxFreq),
                  COUNT: count}
        return retval


def getDataSummaryForAllBands(sensorId,
                              locationMessage,
                              tmin=None,
                              dayCount=None):
    """
    get the summary of the data corresponding to the location message.
    """
    # tmin and tmax are the min and the max of the time range of interest.
    locationMessageId = str(locationMessage["_id"])

    tzId = locationMessage[TIME_ZONE_KEY]
    sensor = SensorDb.getSensor(sensorId)
    if sensor is None:
        return {STATUS: NOK, ERROR_MESSAGE: "Sensor Not found in SensorDb"}
    bands = sensor[THRESHOLDS]
    if len(bands.keys()) == 0:
        return {STATUS: NOK, ERROR_MESSAGE: "Sensor has no bands"}
    measurementType = sensor[MEASUREMENT_TYPE]
    bandStatistics = []
    query = {SENSOR_ID: sensorId, "locationMessageId": locationMessageId}
    msg = DbCollections.getDataMessages(sensorId).find_one(query)
    if msg is None:
        for key in bands.keys():
            band = bands[key]
            minFreq = band[MIN_FREQ_HZ]
            maxFreq = band[MAX_FREQ_HZ]
            sys2detect = band[SYSTEM_TO_DETECT]
            isActive = band[ACTIVE]
            bandInfo = {"tStartDayBoundary": 0,
                        "tEndDayBoundary": 0,
                        "tStartReadings": 0,
                        "tStartLocalTime": 0,
                        "tStartLocalTimeFormattedTimeStamp": UNKNOWN,
                        "tEndReadings": 0,
                        "tEndReadingsLocalTime": 0,
                        "tEndLocalTimeFormattedTimeStamp": UNKNOWN,
                        "tEndDayBoundary": 0,
                        "maxOccupancy": 0,
                        "meanOccupancy": 0,
                        "minOccupancy": 0,
                        "maxFreq": maxFreq,
                        "minFreq": minFreq,
                        SYSTEM_TO_DETECT: sys2detect,
                        "measurementType": measurementType,
                        "active": isActive,
                        COUNT: 0}

            bandStatistics.append(bandInfo)
        return {STATUS: "OK", "bands": bandStatistics}

    if tmin is None and dayCount is None:
        query = {SENSOR_ID: sensorId, "locationMessageId": locationMessageId}
        tmin = msgutils.getDayBoundaryTimeStamp(msg)
        mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(
            int(tmin), tzId)
    elif tmin is not None and dayCount is None:
        mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(
            int(tmin), tzId)
    else:
        mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(
            int(tmin), tzId)

    for key in bands.keys():
        band = bands[key]
        minFreq = band[MIN_FREQ_HZ]
        maxFreq = band[MAX_FREQ_HZ]
        sys2detect = band[SYSTEM_TO_DETECT]
        bandSummary = getBandDataSummary(sensorId,
                                         locationMessage,
                                         sys2detect,
                                         minFreq,
                                         maxFreq,
                                         mintime,
                                         dayCount=dayCount)
        bandStatistics.append(bandSummary)

    return {STATUS: "OK", "bands": bandStatistics}


def getDataSummary(sensorId, latitude, longitude, altitude, tmin=None, dayCount=None):
    """
    Compute and return the data summary for the sensor, given its ID and position.
    """
    locationMessage = DbCollections.getLocationMessages().find_one({SENSOR_ID:sensorId,
                                                                    LON:longitude, LAT:latitude, ALT:altitude})
    if locationMessage is None:
        util.debugPrint("Location Message not found")
        return {STATUS: "NOK", ERROR_MESSAGE: "Location Message Not Found"}
    retval = getSensorDataSummary(sensorId, locationMessage)
    if retval[STATUS] == "OK":
        retval[LOCATION_MESSAGE_ID] = str(locationMessage['_id'])
        bandStats = getDataSummaryForAllBands(sensorId,
                                              locationMessage,
                                              tmin=tmin,
                                              dayCount=dayCount)
        if bandStats[STATUS] == "OK":
            retval[BAND_STATISTICS] = bandStats["bands"]
        else:
            retval = {STATUS: "NOK", ERROR_MESSAGE: bandStats[ERROR_MESSAGE]}
    return retval


def getAcquistionCount(sensorId, lat, lon, alt, sys2detect, minfreq, maxfreq,
                       tAcquistionStart, dayCount):

    """
    Get the acquisition count of a sensor given its location and band of interest.
    """
    locationMessage = DbCollections.getLocationMessages().find_one({SENSOR_ID:sensorId, LAT:lat, LON:lon, ALT:alt})
    if locationMessage is None:
        retval = {COUNT: 0}
        retval[STATUS] = "OK"
        return retval

    freqRange = msgutils.freqRange(sys2detect, minfreq, maxfreq)
    query = {SENSOR_ID: sensorId,
             LOCATION_MESSAGE_ID:str(locationMessage["_id"]),
             "t": {"$gte": tAcquistionStart},
             FREQ_RANGE: freqRange}
    msg = DbCollections.getDataMessages(sensorId).find_one(query)
    if msg is None:
        retval = {COUNT: 0}
        retval[STATUS] = "OK"
        return retval

    startTime = msgutils.getDayBoundaryTimeStamp(msg)

    if dayCount > 0:
        endTime = startTime + SECONDS_PER_DAY * dayCount
        query = {SENSOR_ID: sensorId,
                 LOCATION_MESSAGE_ID:str(locationMessage["_id"]),
                 TIME: {"$gte": startTime},
                 TIME: {"$lte": endTime},
                 FREQ_RANGE: freqRange}
    else:
        query = {SENSOR_ID: sensorId,
                 LOCATION_MESSAGE_ID:str(locationMessage["_id"]),
                 TIME: {"$gte": startTime},
                 FREQ_RANGE: freqRange}

    cur = DbCollections.getDataMessages(sensorId).find(query)
    count = cur.count()

    cur.sort(TIME, pymongo.DESCENDING).limit(2)
    lastMessage = cur.next()
    endTime = msgutils.getDayBoundaryTimeStamp(lastMessage)

    retval = {COUNT: count}
    retval["tStartReadings"] = msg[TIME]
    retval["tEndReadings"] = lastMessage[TIME]
    retval["tStartDayBoundary"] = startTime
    retval["tEndDayBoundary"] = endTime
    query = {SENSOR_ID: sensorId,
             TIME: {"$gte": startTime},
             FREQ_RANGE: freqRange}
    cur = DbCollections.getDataMessages(sensorId).find(query)
    cur.sort(TIME, pymongo.DESCENDING).limit(2)
    lastMessage = cur.next()
    endTime = msgutils.getDayBoundaryTimeStamp(lastMessage)
    retval["tEndReadingsDayBoundary"] = endTime

    retval[STATUS] = "OK"
    return retval

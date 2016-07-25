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
import msgutils
import timezone
import numpy as np
import DbCollections
import DataMessage
import SensorDb

from Defines import SECONDS_PER_DAY
from Defines import SENSOR_ID
from Defines import TIME_ZONE_KEY
from Defines import FFT_POWER
from Defines import FREQ_RANGE
from Defines import CHANNEL_COUNT
from Defines import STATUS
from Defines import ERROR_MESSAGE
from Defines import NOK
from Defines import OK
from Defines import TIME
from Defines import LOCATION_MESSAGE_ID
from Defines import LAT, LON, ALT


def compute_daily_max_min_mean_median_stats_for_swept_freq(
        cursor, subBandMinFreq, subBandMaxFreq):
    meanOccupancy = 0
    minOccupancy = 10000
    maxOccupancy = -1
    count = cursor.count()
    occupancy = []
    n = 0
    if cursor.count() == 0:
        return None
    dayBoundaryTimeStamp = None
    cacheMiss = False
    recomputeOccupancies = False
    insertInCache = True
    cacheVal = None
    for msg in cursor:

        if dayBoundaryTimeStamp is None:
            dayBoundaryTimeStamp = msgutils.getDayBoundaryTimeStamp(msg)

        cutoff = DataMessage.getThreshold(msg)

        if subBandMinFreq == DataMessage.getMinFreq(
                msg) and subBandMaxFreq == DataMessage.getMaxFreq(msg):
            if not cacheMiss:
                freqRange = DataMessage.getFreqRange(msg)
                sensorId = DataMessage.getSensorId(msg)
                cache = DbCollections.getDailyOccupancyCache(sensorId)
                cacheVal = cache.find_one({FREQ_RANGE:freqRange,"dayBoundaryTimeStamp":dayBoundaryTimeStamp})
                if cacheVal is not None:
                    del cacheVal["_id"]
                    insertInCache = False
                    break
                else:
                    recomputeOccupancies = True
                    cacheMiss = True
                    insertInCache = True
            occupancy.append(msg["occupancy"])
        else:
            insertInCache = False
            recomputeOccupancies = True
            # No caching for non-standard cutoff
            powerArray = msgutils.trimSpectrumToSubBand(msg, subBandMinFreq,
                                                        subBandMaxFreq)
            msgOccupancy = float(len(filter(
                lambda x: x >= cutoff, powerArray))) / float(len(powerArray))
            occupancy.append(msgOccupancy)

        n = msg["mPar"]["n"]

    if recomputeOccupancies:
        if len(occupancy) != 0:
            maxOccupancy = float(np.max(occupancy))
            minOccupancy = float(np.min(occupancy))
            meanOccupancy = float(np.mean(occupancy))
        else:
            cutoff = -100
            maxOccupancy = 0
            minOccupancy = 0
            meanOccupancy = 0

    if recomputeOccupancies:
        cacheVal = {"count": count,
                    "dayBoundaryTimeStamp":dayBoundaryTimeStamp,
                    "maxOccupancy":maxOccupancy,
                    "minOccupancy":minOccupancy,
                    "meanOccupancy":meanOccupancy}

    if insertInCache:
        cacheVal[FREQ_RANGE] = freqRange
        cache = DbCollections.getDailyOccupancyCache(sensorId)
        cache.insert(cacheVal, upsert=False)

    if "_id" in cacheVal:
        del cacheVal["_id"]

    return (cutoff, cacheVal)


# Compute the daily max min and mean stats. The cursor starts on a day
# boundary and ends on a day boundary.
def compute_daily_max_min_mean_stats_for_fft_power(cursor):
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
        if dayBoundaryTimeStamp is None:
            dayBoundaryTimeStamp = msgutils.getDayBoundaryTimeStamp(msg)
        minFreq = msg["mPar"]["fStart"]
        maxFreq = msg["mPar"]["fStop"]
        cutoff = msg["cutoff"]
        maxOccupancy = np.maximum(maxOccupancy, msg["maxOccupancy"])
        minOccupancy = np.minimum(minOccupancy, msg["minOccupancy"])
        meanOccupancy = meanOccupancy + msg["meanOccupancy"]
    meanOccupancy = float(meanOccupancy) / float(nReadings)
    return (cutoff, {"count": count,
                     "dayBoundaryTimeStamp": dayBoundaryTimeStamp,
                     "maxOccupancy":maxOccupancy,
                     "minOccupancy":minOccupancy,
                     "meanOccupancy":meanOccupancy})


def getDailyMaxMinMeanStats(sensorId, lat, lon, alt, tstart, ndays, sys2detect, fmin,
                            fmax, subBandMinFreq, subBandMaxFreq):

    locationMessage = DbCollections.getLocationMessages().find_one({SENSOR_ID:sensorId, LAT:lat, LON:lon, ALT:alt})
    if locationMessage is None:
        return {STATUS: NOK, ERROR_MESSAGE: "Location Information Not Found"}
    locationMessageId = str(locationMessage["_id"])
    tZId = locationMessage[TIME_ZONE_KEY]
    tmin = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(tstart, tZId)
    startMessage = DbCollections.getDataMessages(sensorId).find_one()
    result = {}
    result[STATUS] = OK
    values = {}
    for day in range(0, ndays):
        tstart = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(tmin + day * SECONDS_PER_DAY, tZId)
        tend = tstart + SECONDS_PER_DAY
        queryString = {LOCATION_MESSAGE_ID:locationMessageId, TIME: {'$gte':tstart, '$lte': tend},
                       FREQ_RANGE:msgutils.freqRange(sys2detect, fmin, fmax)}
        cur = DbCollections.getDataMessages(sensorId).find(queryString)
        # cur.batch_size(20)
        if startMessage['mType'] == FFT_POWER:
            stats = compute_daily_max_min_mean_stats_for_fft_power(cur)
        else:
            stats = compute_daily_max_min_mean_median_stats_for_swept_freq(
                cur, subBandMinFreq, subBandMaxFreq)
        # gap in readings. continue.
        if stats is None:
            continue
        (cutoff, dailyStat) = stats
        values[day * 24] = dailyStat
    # Now compute the next interval after the last one (if one exists)
    tend = tmin + SECONDS_PER_DAY * ndays
    queryString = {LOCATION_MESSAGE_ID: locationMessageId, TIME: {'$gte':tend},
                   FREQ_RANGE:msgutils.freqRange(sys2detect, fmin, fmax)}
    msg = DbCollections.getDataMessages(sensorId).find_one(queryString)
    if msg is None:
        result["nextTmin"] = tmin
    else:
        nextTmin = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg[TIME],
                                                                    tZId)
        result["nextTmin"] = nextTmin
    # Now compute the previous interval before this one.
    prevMessage = msgutils.getPrevAcquisition(startMessage)
    if prevMessage is not None:
        newTmin = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(
            prevMessage[TIME] - SECONDS_PER_DAY * ndays, tZId)
        queryString = {LOCATION_MESSAGE_ID:locationMessageId, TIME: {'$gte':newTmin},
                       FREQ_RANGE:msgutils.freqRange(sys2detect, fmin, fmax)}
        msg = DbCollections.getDataMessages(sensorId).find_one(queryString)
    else:
        msg = startMessage
    sensor = SensorDb.getSensorObj(sensorId)
    channelCount = sensor.getChannelCount(sys2detect,fmin,fmax)
    result[STATUS] = OK
    result["prevTmin"] = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(
        msg[TIME], tZId)
    result["tmin"] = tmin
    result["maxFreq"] = fmin
    result["minFreq"] = fmax
    result["cutoff"] = cutoff
    result[CHANNEL_COUNT] = channelCount
    result["startDate"] = timezone.formatTimeStampLong(tmin, tZId)
    result["values"] = values
    util.debugPrint(result)
    return result

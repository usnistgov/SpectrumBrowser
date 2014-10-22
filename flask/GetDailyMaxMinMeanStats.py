import flaskr as globals
import populate_db
import util
from flaskr import make_response
import msgutils
import timezone
import numpy as np
from flask import jsonify

def compute_daily_max_min_mean_median_stats_for_swept_freq(cursor, subBandMinFreq, subBandMaxFreq):
    meanOccupancy = 0
    minOccupancy = 10000
    maxOccupancy = -1
    occupancy = []
    n = 0
    for msg in cursor:
        cutoff = msg["cutoff"]
        powerArray = msgutils.trimSpectrumToSubBand(msg, subBandMinFreq, subBandMaxFreq)
        msgOccupancy = float(len(filter(lambda x: x >= cutoff, powerArray))) / float(len(powerArray))
        occupancy.append(msgOccupancy)
        n = msg["mPar"]["n"]

    if len(occupancy) != 0:
        maxOccupancy = float(np.max(occupancy))
        minOccupancy = float(np.min(occupancy))
        meanOccupancy = float(np.mean(occupancy))
        medianOccupancy = float(np.median(occupancy))
    else:
        cutoff = -100
        maxOccupancy = 0
        minOccupancy = 0
        meanOccupancy = 0
        medianOccupancy = 0

    retval = (n, subBandMaxFreq, subBandMinFreq, cutoff, \
        {"maxOccupancy":util.roundTo3DecimalPlaces(maxOccupancy), "minOccupancy":util.roundTo3DecimalPlaces(minOccupancy), \
        "meanOccupancy":util.roundTo3DecimalPlaces(meanOccupancy), "medianOccupancy":util.roundTo3DecimalPlaces(medianOccupancy)})
    util.debugPrint(retval)
    return retval

# Compute the daily max min and mean stats. The cursor starts on a day
# boundary and ends on a day boundary.
def compute_daily_max_min_mean_stats_for_fft_power(cursor):
    util.debugPrint("compute_daily_max_min_mean_stats_for_fft_power")
    meanOccupancy = 0
    minOccupancy = 10000
    maxOccupancy = -1
    nReadings = cursor.count()
    print "nreadings" , nReadings
    if nReadings == 0:
        util.debugPrint ("zero count")
        return None
    for msg in cursor:
        n = msg["mPar"]["n"]
        minFreq = msg["mPar"]["fStart"]
        maxFreq = msg["mPar"]["fStop"]
        cutoff = msg["cutoff"]
        if msg["mType"] == "FFT-Power" :
            maxOccupancy = np.maximum(maxOccupancy, msg["maxOccupancy"])
            minOccupancy = np.minimum(minOccupancy, msg["minOccupancy"])
            meanOccupancy = meanOccupancy + msg["meanOccupancy"]
        else:
            maxOccupancy = np.maximum(maxOccupancy, msg["occupancy"])
            minOccupancy = np.minimum(maxOccupancy, msg["occupancy"])
            meanOccupancy = meanOccupancy + msg["occupancy"]
    meanOccupancy = float(meanOccupancy) / float(nReadings)
    return (n, maxFreq, minFreq, cutoff, \
        {"maxOccupancy":util.roundTo3DecimalPlaces(maxOccupancy), "minOccupancy":util.roundTo3DecimalPlaces(minOccupancy), \
        "meanOccupancy":util.roundTo3DecimalPlaces(meanOccupancy)})


def  getDailyMaxMinMeanStats(sensorId, startTime, dayCount, sys2detect, fmin, \
                             fmax,subBandMinFreq,subBandMaxFreq, sessionId):
    tstart = int(startTime)
    ndays = int(dayCount)
    fmin = int(fmin)
    fmax = int(fmax)
    queryString = { globals.SENSOR_ID : sensorId, "t" : {'$gte':tstart},\
                   "freqRange": populate_db.freqRange(sys2detect, fmin, fmax)}
    startMessage = globals.db.dataMessages.find_one(queryString)
    if startMessage == None:
        errorStr = "Start Message Not Found"
        util.debugPrint(errorStr)
        response = make_response(util.formatError(errorStr), 404)
        return response
    locationMessage = msgutils.getLocationMessage(startMessage)
    tZId = locationMessage[globals.TIME_ZONE_KEY]
    if locationMessage == None:
        errorStr = "Location Message Not Found"
        util.debugPrint(errorStr)
        response = make_response(util.formatError(errorStr), 404)
    tmin = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(startMessage['t'], tZId)
    result = {}
    values = {}
    for day in range(0, ndays):
        tstart = tmin + day * globals.SECONDS_PER_DAY
        tend = tstart + globals.SECONDS_PER_DAY
        queryString = { globals.SENSOR_ID : sensorId, "t" : {'$gte':tstart, '$lte': tend},\
                       "freqRange":populate_db.freqRange(sys2detect,fmin, fmax)}
        cur = globals.db.dataMessages.find(queryString)
        cur.batch_size(20)
        if startMessage['mType'] == "FFT-Power":
            stats = compute_daily_max_min_mean_stats_for_fft_power(cur)
        else:
            stats = compute_daily_max_min_mean_median_stats_for_swept_freq(cur, subBandMinFreq, subBandMaxFreq)
        # gap in readings. continue.
        if stats == None:
            continue
        (nChannels, maxFreq, minFreq, cutoff, dailyStat) = stats
        values[day * 24] = dailyStat
    result["tmin"] = tmin
    result["maxFreq"] = maxFreq
    result["minFreq"] = minFreq
    result["cutoff"] = cutoff
    result["channelCount"] = nChannels
    result["startDate"] = timezone.formatTimeStampLong(tmin, tZId)
    result["values"] = values
    util.debugPrint(result)
    return jsonify(result)

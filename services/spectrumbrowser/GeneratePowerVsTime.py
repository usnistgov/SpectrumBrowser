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
import matplotlib.pyplot as plt
from flask import request
from Defines import TIME_ZONE_KEY
from Defines import SENSOR_ID
from Defines import SECONDS_PER_DAY
from Defines import STATIC_GENERATED_FILE_LOCATION
from Defines import MILISECONDS_PER_SECOND
from Defines import OK
from Defines import STATUS
from Defines import ERROR_MESSAGE
from Defines import NOK
from Defines import CHART_WIDTH
from Defines import CHART_HEIGHT

import Config
import DbCollections


def generatePowerVsTimeForSweptFrequency(sensorId, startTime, freqHz,
                                         sessionId):
    """
    generate a power vs. time plot for swept frequency readings.
    The plot is generated for a period of one day.
    """
    chWidth = Config.getScreenConfig()[CHART_WIDTH]
    chHeight = Config.getScreenConfig()[CHART_HEIGHT]

    dataMessages = DbCollections.getDataMessages(sensorId)
    if dataMessages is None:
        return {STATUS: NOK,
                ERROR_MESSAGE: "Data Message Collection not found"}
    msg = dataMessages.find_one({SENSOR_ID: sensorId,
                                 "t": {"$gt": int(startTime)}})
    (maxFreq, minFreq) = msgutils.getMaxMinFreq(msg)
    locationMessage = msgutils.getLocationMessage(msg)
    timeZone = locationMessage[TIME_ZONE_KEY]
    if freqHz > maxFreq:
        freqHz = maxFreq
    if freqHz < minFreq:
        freqHz = minFreq
    n = int(msg["mPar"]["n"])
    freqIndex = int(float(freqHz - minFreq) / float(maxFreq - minFreq) *
                    float(n))
    powerArray = []
    timeArray = []
    startTime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg['t'],
                                                                 timeZone)
    while True:
        data = msgutils.getData(msg)
        powerArray.append(data[freqIndex])
        timeArray.append(float(msg['t'] - startTime) / float(3600))
        nextMsg = msgutils.getNextAcquisition(msg)
        if nextMsg is None:
            break
        elif nextMsg['t'] - startTime > SECONDS_PER_DAY:
            break
        else:
            msg = nextMsg

    plt.figure(figsize=(chWidth, chHeight))
    plt.xlim([0, 23])
    freqMHz = float(freqHz) / 1E6
    title = "Power vs. Time at " + str(freqMHz) + " MHz"
    plt.title(title)
    xlabel = "Time (H) from start of day"
    plt.xlabel(xlabel)
    ylabel = "Signal Power (dBm)"
    plt.ylabel(ylabel)
    plt.xlim([0, 23])
    plt.scatter(timeArray, powerArray)
    spectrumFile = sessionId + "/" + msg[SENSOR_ID] + "." + str(
        startTime) + "." + str(freqMHz) + ".power.png"
    spectrumFilePath = util.getPath(
        STATIC_GENERATED_FILE_LOCATION) + spectrumFile
    plt.savefig(spectrumFilePath, pad_inches=0, dpi=100)
    plt.clf()
    plt.close()
    retval = {STATUS : OK, "powervstime" : Config.getGeneratedDataPath() + "/" + spectrumFile,"timeArray":timeArray,\
  "powerValues":powerArray, "title":title,"xlabel":xlabel,"ylabel":ylabel}
    return retval


# Generate power vs. time plot for FFTPower type data.
# given a frequency in MHz
def generatePowerVsTimeForFFTPower(sensorId, startTime, leftBound, rightBound,
                                   freqHz, sessionId):
    """
    Generate a power vs. time plot for FFTPower readings. The plot is generated for one acquistion.
    """
    chWidth = Config.getScreenConfig()[CHART_WIDTH]
    chHeight = Config.getScreenConfig()[CHART_HEIGHT]
    msg = DbCollections.getDataMessages(sensorId).find_one(
        {SENSOR_ID: sensorId,
         "t": int(startTime)})
    if msg is None:
        errorMessage = "Message not found"
        util.debugPrint(errorMessage)
        return {STATUS: NOK, ERROR_MESSAGE: errorMessage}
    n = int(msg["mPar"]["n"])
    measurementDuration = msg["mPar"]["td"]
    miliSecondsPerMeasurement = float(
        measurementDuration * MILISECONDS_PER_SECOND) / float(msg["nM"])
    leftColumnsToExclude = int(leftBound / miliSecondsPerMeasurement)
    rightColumnsToExclude = int(rightBound / miliSecondsPerMeasurement)
    if leftColumnsToExclude + rightColumnsToExclude >= msg["nM"]:
        util.debugPrint("leftColumnToExclude " + str(leftColumnsToExclude) +
                        " rightColumnsToExclude " + str(rightColumnsToExclude))
        return None
    nM = int(msg["nM"]) - leftColumnsToExclude - rightColumnsToExclude
    power = np.array(msgutils.getData(msg))
    lengthToRead = int(n * msg["nM"])
    powerVal = power[n * leftColumnsToExclude:lengthToRead - n *
                     rightColumnsToExclude]
    spectrogramData = np.transpose(powerVal.reshape(nM, n))
    maxFreq = msg["mPar"]["fStop"]
    minFreq = msg["mPar"]["fStart"]
    freqDeltaPerIndex = float(maxFreq - minFreq) / float(n)
    row = int((freqHz - minFreq) / freqDeltaPerIndex)
    util.debugPrint("row = " + str(row))
    if row < 0:
        util.debugPrint("WARNING: row < 0")
        row = 0
    powerValues = spectrogramData[row, :]
    timeArray = [float((leftColumnsToExclude + i) * miliSecondsPerMeasurement)
                 / float(MILISECONDS_PER_SECOND) for i in range(0, nM)]
    plt.figure(figsize=(chWidth, chHeight))
    plt.xlim([float(leftBound) / float(MILISECONDS_PER_SECOND), \
              float(measurementDuration * MILISECONDS_PER_SECOND - rightBound) / float(MILISECONDS_PER_SECOND)])
    plt.scatter(timeArray, powerValues)

    freqMHz = float(freqHz) / 1E6
    title = "Power vs. Time at " + str(freqMHz) + " MHz"
    plt.title(title)
    spectrumFile = sessionId + "/" + msg[SENSOR_ID] + "." + str(startTime) + "." + str(leftBound) + "." + str(rightBound) \
        + "." + str(freqMHz) + ".power.png"
    spectrumFilePath = util.getPath(
        STATIC_GENERATED_FILE_LOCATION) + spectrumFile
    xlabel = "Time (s) from start of acquistion"
    ylabel = "Signal Power (dBm)"
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.savefig(spectrumFilePath, pad_inches=0, dpi=100)
    plt.clf()
    plt.close()
    retval = {"powervstime" : Config.getGeneratedDataPath() + "/" + spectrumFile,"powerValues":powerValues.tolist(),\
 "timeArray": timeArray,"title":title,"xlabel":xlabel,"ylabel":ylabel}
    retval[STATUS] = OK
    return retval

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


import matplotlib.pyplot as plt
import util
import msgutils
import numpy as np
import timezone
import sys
import traceback
from bson.objectid import ObjectId
import DbCollections
from Defines import TIME_ZONE_KEY
from Defines import SENSOR_ID
from Defines import STATIC_GENERATED_FILE_LOCATION
from Defines import MILISECONDS_PER_SECOND
from Defines import CHART_WIDTH
from Defines import CHART_HEIGHT
from Defines import NOISE_FLOOR

import Config


def generateSpectrumForSweptFrequency(msg, sessionId, minFreq, maxFreq):
    try:
        chWidth = Config.getScreenConfig()[CHART_WIDTH]
        chHeight = Config.getScreenConfig()[CHART_HEIGHT]

        spectrumData = msgutils.trimSpectrumToSubBand(msg, minFreq, maxFreq)
        noiseFloorData = msgutils.trimNoiseFloorToSubBand(msg, minFreq,
                                                          maxFreq)
        nSteps = len(spectrumData)
        freqDelta = float(maxFreq - minFreq) / float(1E6) / nSteps
        freqArray = [float(minFreq) / float(1E6) + i * freqDelta
                     for i in range(0, nSteps)]
        plt.figure(figsize=(chWidth, chHeight))
        plt1 = plt.scatter(freqArray,
                           spectrumData,
                           color='red',
                           label="Signal Power")
        plt2 = plt.scatter(freqArray,
                           noiseFloorData,
                           color='black',
                           label="Noise Floor")
        plt.legend(handles=[plt1, plt2])
        xlabel = "Freq (MHz)"
        plt.xlabel(xlabel)
        ylabel = "Power (dBm)"
        plt.ylabel(ylabel)
        locationMessage = DbCollections.getLocationMessages().find_one(
            {"_id": ObjectId(msg["locationMessageId"])})
        t = msg["t"]
        tz = locationMessage[TIME_ZONE_KEY]
        title = "Spectrum at " + timezone.formatTimeStampLong(t, tz)
        plt.title(title)
        spectrumFile = sessionId + "/" + msg[SENSOR_ID] + "." + str(msg[
            't']) + "." + str(minFreq) + "." + str(maxFreq) + ".spectrum.png"
        spectrumFilePath = util.getPath(
            STATIC_GENERATED_FILE_LOCATION) + spectrumFile
        plt.savefig(spectrumFilePath, pad_inches=0, dpi=100)
        plt.clf()
        plt.close()
        # plt.close("all")
        urlPrefix = Config.getGeneratedDataPath()
        retval = {"status" : "OK", "spectrum" : urlPrefix + "/" + spectrumFile ,"freqArray":freqArray,\
  "spectrumData":spectrumData.tolist(),"noiseFloorData":noiseFloorData.tolist(),"title":title,\
  "xlabel":xlabel, "ylabel":ylabel}
        return retval
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise


# generate the spectrum for a FFT power acquisition at a given milisecond offset.
# from the start time.
def generateSpectrumForFFTPower(msg, milisecOffset, sessionId):
    chWidth = Config.getScreenConfig()[CHART_WIDTH]
    chHeight = Config.getScreenConfig()[CHART_HEIGHT]

    startTime = msg["t"]
    nM = int(msg["nM"])
    n = int(msg["mPar"]["n"])
    measurementDuration = int(msg["mPar"]["td"])
    miliSecondsPerMeasurement = float(measurementDuration *
                                      MILISECONDS_PER_SECOND) / float(nM)
    powerVal = np.array(msgutils.getData(msg))
    spectrogramData = np.transpose(powerVal.reshape(nM, n))
    col = int(milisecOffset / miliSecondsPerMeasurement)
    util.debugPrint("Col = " + str(col))
    spectrumData = spectrogramData[:, col]
    maxFreq = msg["mPar"]["fStop"]
    minFreq = msg["mPar"]["fStart"]
    nSteps = len(spectrumData)
    freqDelta = float(maxFreq - minFreq) / float(1E6) / nSteps
    freqArray = [float(minFreq) / float(1E6) + i * freqDelta
                 for i in range(0, nSteps)]
    plt.figure(figsize=(chWidth, chHeight))
    plt.scatter(freqArray, spectrumData, color='red', label='Signal Power')
    # TODO -- fix this when the sensor is calibrated.
    wnI = msg[NOISE_FLOOR]
    noiseFloorData = [wnI for i in range(0, len(spectrumData))]
    plt.scatter(freqArray, noiseFloorData, color='black', label="Noise Floor")
    xlabel = "Freq (MHz)"
    ylabel = "Power (dBm)"
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    locationMessage = DbCollections.getLocationMessages().find_one(
        {"_id": ObjectId(msg["locationMessageId"])})
    t = msg["t"] + milisecOffset / float(MILISECONDS_PER_SECOND)
    tz = locationMessage[TIME_ZONE_KEY]
    title = "Spectrum at " + timezone.formatTimeStampLong(t, tz)
    plt.title(title)
    spectrumFile = sessionId + "/" + msg[SENSOR_ID] + "." + str(
        startTime) + "." + str(milisecOffset) + ".spectrum.png"
    spectrumFilePath = util.getPath(
        STATIC_GENERATED_FILE_LOCATION) + spectrumFile
    plt.savefig(spectrumFilePath, pad_inches=0, dpi=100)
    plt.clf()
    plt.close()
    # plt.close("all")
    retval = {"status" : "OK", "spectrum" : Config.getGeneratedDataPath() + "/" + spectrumFile , "freqArray":freqArray, \
  "spectrumData":spectrumData.tolist(),"noiseFloorData":noiseFloorData,"title":title,\
  "xlabel":xlabel,"ylabel":ylabel}
    return retval

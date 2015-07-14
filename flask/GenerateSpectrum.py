
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

import Config


def generateSpectrumForSweptFrequency(msg, sessionId, minFreq, maxFreq):
    try:
        chWidth = Config.getScreenConfig()[CHART_WIDTH]
        chHeight = Config.getScreenConfig()[CHART_HEIGHT]
        
        spectrumData = msgutils.trimSpectrumToSubBand(msg, minFreq, maxFreq)
        nSteps = len(spectrumData)
        freqDelta = float(maxFreq - minFreq) / float(1E6) / nSteps
        freqArray = [ float(minFreq) / float(1E6) + i * freqDelta for i in range(0, nSteps)]
        plt.figure(figsize=(chWidth, chHeight))
        plt.scatter(freqArray, spectrumData)
        plt.xlabel("Freq (MHz)")
        plt.ylabel("Power (dBm)")
        locationMessage = DbCollections.getLocationMessages().find_one({"_id": ObjectId(msg["locationMessageId"])})
        t = msg["t"]
        tz = locationMessage[TIME_ZONE_KEY]
        plt.title("Spectrum at " + timezone.formatTimeStampLong(t, tz))
        spectrumFile = sessionId + "/" + msg[SENSOR_ID] + "." + str(msg['t']) + "." + str(minFreq) + "." + str(maxFreq) + ".spectrum.png"
        spectrumFilePath = util.getPath(STATIC_GENERATED_FILE_LOCATION) + spectrumFile
        plt.savefig(spectrumFilePath, pad_inches=0, dpi=100)
        plt.clf()
        plt.close()
        # plt.close("all")
        urlPrefix = Config.getGeneratedDataPath()
        retval = {"status" : "OK", "spectrum" : urlPrefix + "/" + spectrumFile }
        util.debugPrint(retval)
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
    miliSecondsPerMeasurement = float(measurementDuration * MILISECONDS_PER_SECOND) / float(nM)
    powerVal = msgutils.getData(msg)
    spectrogramData = np.transpose(powerVal.reshape(nM, n))
    col = int(milisecOffset / miliSecondsPerMeasurement)
    util.debugPrint("Col = " + str(col))
    spectrumData = spectrogramData[:, col]
    maxFreq = msg["mPar"]["fStop"]
    minFreq = msg["mPar"]["fStart"]
    nSteps = len(spectrumData)
    freqDelta = float(maxFreq - minFreq) / float(1E6) / nSteps
    freqArray = [ float(minFreq) / float(1E6) + i * freqDelta for i in range(0, nSteps)]
    plt.figure(figsize=(chWidth, chHeight))
    plt.scatter(freqArray, spectrumData)
    plt.xlabel("Freq (MHz)")
    plt.ylabel("Power (dBm)")
    locationMessage = DbCollections.getLocationMessages().find_one({"_id": ObjectId(msg["locationMessageId"])})
    t = msg["t"] + milisecOffset / float(MILISECONDS_PER_SECOND)
    tz = locationMessage[TIME_ZONE_KEY]
    plt.title("Spectrum at " + timezone.formatTimeStampLong(t, tz))
    spectrumFile = sessionId + "/" + msg[SENSOR_ID] + "." + str(startTime) + "." + str(milisecOffset) + ".spectrum.png"
    spectrumFilePath = util.getPath(STATIC_GENERATED_FILE_LOCATION) + spectrumFile
    plt.savefig(spectrumFilePath, pad_inches=0, dpi=100)
    plt.clf()
    plt.close()
    # plt.close("all")
    retval = {"status" : "OK", "spectrum" : Config.getGeneratedDataPath() + "/" + spectrumFile }
    util.debugPrint(retval)
    return retval


import util
import msgutils
import timezone
import numpy as np
import matplotlib.pyplot as plt
from flask import jsonify
from flask import request
from Defines import TIME_ZONE_KEY
from Defines import SENSOR_ID
from Defines import SECONDS_PER_DAY
import Config

def generatePowerVsTimeForSweptFrequency(msg, freqHz, sessionId):
    """
    generate a power vs. time plot for swept frequency readings.
    The plot is generated for a period of one day.
    """
    (maxFreq, minFreq) = msgutils.getMaxMinFreq(msg)
    locationMessage = msgutils.getLocationMessage(msg)
    timeZone = locationMessage[TIME_ZONE_KEY]
    if freqHz > maxFreq:
        freqHz = maxFreq
    if freqHz < minFreq:
        freqHz = minFreq
    n = msg["mPar"]["n"]
    freqIndex = int(float(freqHz - minFreq) / float(maxFreq - minFreq) * float(n))
    powerArray = []
    timeArray = []
    startTime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg['t'], timeZone)
    while True:
        data = msgutils.getData(msg)
        powerArray.append(data[freqIndex])
        timeArray.append(float(msg['t'] - startTime) / float(3600))
        nextMsg = msgutils.getNextAcquisition(msg)
        if nextMsg == None:
            break
        elif nextMsg['t'] - startTime > SECONDS_PER_DAY:
            break
        else:
            msg = nextMsg

    plt.figure(figsize=(6, 4))
    plt.xlim([0, 23])
    freqMHz = float(freqHz) / 1E6
    plt.title("Power vs. Time at " + str(freqMHz) + " MHz")
    plt.xlabel("Time from start of day (Hours)")
    plt.ylabel("Power (dBm)")
    plt.xlim([0, 23])
    plt.scatter(timeArray, powerArray)
    spectrumFile = sessionId + "/" + msg[SENSOR_ID] + "." + str(startTime) + "." + str(freqMHz) + ".power.png"
    spectrumFilePath = util.getPath("static/generated/") + spectrumFile
    plt.savefig(spectrumFilePath, pad_inches=0, dpi=100)
    plt.clf()
    plt.close()
    retval = {"Status" : "OK" , "powervstime" : Config.getGeneratedDataPath() + "/" + spectrumFile }
    util.debugPrint(retval)
    return jsonify(retval)



# Generate power vs. time plot for FFTPower type data.
# given a frequency in MHz
def generatePowerVsTimeForFFTPower(msg, freqHz, sessionId):
    """
    Generate a power vs. time plot for FFTPower readings. The plot is generated for one acquistion.
    """
    startTime = msg["t"]
    n = msg["mPar"]["n"]
    leftBound = float(request.args.get("leftBound", 0))
    rightBound = float(request.args.get("rightBound", 0))
    if leftBound < 0 or rightBound < 0 :
        util.debugPrint("Bounds to exlude must be >= 0")
        return None
    measurementDuration = msg["mPar"]["td"]
    miliSecondsPerMeasurement = float(measurementDuration * 1000) / float(msg["nM"])
    leftColumnsToExclude = int(leftBound / miliSecondsPerMeasurement)
    rightColumnsToExclude = int(rightBound / miliSecondsPerMeasurement)
    if leftColumnsToExclude + rightColumnsToExclude >= msg["nM"]:
        util.debugPrint("leftColumnToExclude " + str(leftColumnsToExclude) + " rightColumnsToExclude " + str(rightColumnsToExclude))
        return None
    nM = msg["nM"] - leftColumnsToExclude - rightColumnsToExclude
    power = msgutils.getData(msg)
    lengthToRead = n * msg["nM"]
    powerVal = power[n * leftColumnsToExclude:lengthToRead - n * rightColumnsToExclude]
    spectrogramData = np.transpose(powerVal.reshape(nM, n))
    maxFreq = msg["mPar"]["fStop"]
    minFreq = msg["mPar"]["fStart"]
    freqDeltaPerIndex = float(maxFreq - minFreq) / float(n)
    row = int((freqHz - minFreq) / freqDeltaPerIndex)
    util.debugPrint("row = " + str(row))
    if  row < 0 :
        util.debugPrint("WARNING: row < 0")
        row = 0
    powerValues = spectrogramData[row, :]
    timeArray = [(leftColumnsToExclude + i) * miliSecondsPerMeasurement for i in range(0, nM)]
    plt.figure(figsize=(6, 4))
    plt.xlim([leftBound, measurementDuration * 1000 - rightBound])
    plt.scatter(timeArray, powerValues)
    freqMHz = float(freqHz) / 1E6
    plt.title("Power vs. Time at " + str(freqMHz) + " MHz")
    spectrumFile = sessionId + "/" + msg[SENSOR_ID] + "." + str(startTime) + "." + str(leftBound) + "." + str(rightBound) \
        + "." + str(freqMHz) + ".power.png"
    spectrumFilePath = util.getPath("static/generated/") + spectrumFile
    plt.xlabel("Time from start of acquistion (ms)")
    plt.ylabel("Power (dBm)")
    plt.savefig(spectrumFilePath, pad_inches=0, dpi=100)
    plt.clf()
    plt.close()
    retval = {"powervstime" : Config.getGeneratedDataPath() + "/" + spectrumFile }
    util.debugPrint(retval)
    return jsonify(retval)

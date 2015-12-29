'''
Created on Feb 9, 2015

@author: local
'''
from Defines import DATA_TYPE
from Defines import NOISE_FLOOR
from Defines import DATA_KEY
from Defines import SENSOR_ID
from Defines import SYS_TO_DETECT
from Defines import THRESHOLD_DBM_PER_HZ
from Defines import THRESHOLD_MIN_FREQ_HZ
from Defines import THRESHOLD_MAX_FREQ_HZ
from Defines import THRESHOLD_SYS_TO_DETECT
from Defines import OCCUPANCY_KEY, OCCUPANCY_VECTOR_LENGTH
from Defines import FREQ_RANGE
from Defines import ACTIVE

from Defines import FFT_POWER
from Sensor import Sensor
import Message
import DbCollections
import numpy as np
import msgutils
import math
import util

    
def init(jsonData):
    threshold = _getThreshold(jsonData)
    if threshold == None:
        util.errorPrint("Threshold not set for " + str(jsonData))
        raise Exception("Threshold not set - configuration error")
    jsonData['cutoff'] = int(threshold)
    jsonData[FREQ_RANGE] = _getFreqRange(jsonData)
    
    
def getThreshold(jsonData):
    return int(jsonData['cutoff'])

def getFreqRange(jsonData):
    return jsonData[FREQ_RANGE]

def resetThreshold(jsonData):
    newThreshold = _getThreshold(jsonData)
    if newThreshold != getThreshold(jsonData):
        jsonData['cutoff'] = newThreshold
        cutoff = newThreshold
        powerVal = msgutils.getData(jsonData)
        n = getNumberOfFrequencyBins(jsonData)
        nM = getNumberOfMeasurements(jsonData)
        if getMeasurementType(jsonData) == FFT_POWER :
            occupancyCount = [0 for i in range(0, nM)]
            # unpack the power array.
            powerArray = powerVal.reshape(nM, n)
            for i in range(0, nM):
                occupancyCount[i] = float(len(filter(lambda x: x >= cutoff, powerArray[i, :]))) / float(n)
            setMaxOccupancy(jsonData, float(np.max(occupancyCount)))
            setMeanOccupancy(jsonData, float(np.mean(occupancyCount)))
            setMinOccupancy(jsonData, float(np.min(occupancyCount)))
            setMedianOccupancy(jsonData, float(np.median(occupancyCount)))
        else:
            occupancyCount = float(len(filter(lambda x: x >= cutoff, powerVal)))
            setOccupancy(jsonData, occupancyCount / float(len(powerVal)))
        return True
    else:
        return False

    
def _getThreshold(jsonData):
    sensor = Sensor(DbCollections.getSensors().find_one({SENSOR_ID:Message.getSensorId(jsonData)}))
    thresholds = sensor.getThreshold()
    sys2Detect = getSys2Detect(jsonData)
    for thresholdKey in thresholds.keys():
        threshold = thresholds[thresholdKey]
        if threshold[THRESHOLD_SYS_TO_DETECT] == sys2Detect and \
            threshold[THRESHOLD_MIN_FREQ_HZ] == getFmin(jsonData) and \
            threshold[THRESHOLD_MAX_FREQ_HZ] == getFmax(jsonData) and \
	    threshold["active"] == True:
            actualThreshold = threshold[THRESHOLD_DBM_PER_HZ] + 10 * math.log10(getResolutionBandwidth(jsonData))
            if actualThreshold < 0 :
                actualThreshold = int(actualThreshold - 0.5)
            else:
                actualThreshold = int(actualThreshold + 0.5)
            return actualThreshold
    return None     
        
    
def setLocationMessageId(jsonData, locationMessageId):
    jsonData["locationMessageId"] = locationMessageId
      
def getLocationMessageId(jsonData):
    return jsonData["locationMessageId"]

def setSystemMessageId(jsonData, systemMessageId):
    jsonData["systemMessageId"] = systemMessageId
    
def getSystemMessageId(jsonData):
    return jsonData["systemMessageId"]

def setSecondsPerFrame(jsonData, secondsPerFrame):
    jsonData["_secondsPerFrame"] = secondsPerFrame

def getSecondsPerFrame(jsonData):
    return jsonData["_secondsPerFrame"]
    
def getNumberOfMeasurements(jsonData):
    return int(jsonData["nM"])

def setDataKey(jsonData, key):
    jsonData[DATA_KEY] = str(key)
    
def getDataKey(jsonData):
    return jsonData[DATA_KEY]

def setOccupancyKey(jsonData, key):
    jsonData[OCCUPANCY_KEY] = str(key)
    
def setOccupancyVectorLength(jsonData, length):
    jsonData[OCCUPANCY_VECTOR_LENGTH] = length
    
def getOccupancyVectorLength(jsonData):
    return jsonData[OCCUPANCY_VECTOR_LENGTH]
    
def getOccupancyKey(jsonData):
    return jsonData[OCCUPANCY_KEY]

def getNumberOfFrequencyBins(jsonData):
    return int(jsonData["mPar"]["n"])


# For streaming
def getTimePerMeasurement(jsonData):
    return jsonData["mPar"]["tm"]

def getFmax(jsonData):
    return jsonData["mPar"]["fStop"]

def getFmin(jsonData):
    return jsonData["mPar"]["fStart"]

def getResolutionBandwidth(jsonData):
    if getMeasurementType(jsonData) == FFT_POWER:
        return int((getFmax(jsonData) - getFmin(jsonData)) / getNumberOfFrequencyBins(jsonData))
    else:
        sysMessage = DbCollections.getSystemMessages().find_one({SENSOR_ID:getSensorId(jsonData)})
        return sysMessage["Cal"]["mPar"]["RBW"]
    
def _getFreqRange(jsonData):
    sys2detect = jsonData["Sys2Detect"]
    fmin = jsonData["mPar"]['fStart']
    fmax = jsonData["mPar"]['fStop']
    return freqRange(sys2detect, fmin, fmax)

def freqRange(sys2detect, fmin, fmax):
    sd = sys2detect.replace(" ", "").replace(":", "")
    return sd + ":" + str(int(fmin)) + ":" + str(int(fmax))

def getDataType(jsonData):
    return jsonData[DATA_TYPE]

def getNoiseFloor(jsonData):
    return jsonData[NOISE_FLOOR]

def getSensorId(jsonData):
    return Message.getSensorId(jsonData)

def getTime(jsonData):
    return Message.getTime(jsonData)

def setTime(jsonData, time):
    jsonData["t"] = time

def getSys2Detect(jsonData):
    return jsonData[SYS_TO_DETECT]

def getMeasurementDuration(jsonData):
    return jsonData["mPar"]["td"]

def getMeasurementType(jsonData):
    return jsonData["mType"]

def setMaxOccupancy(jsonData, occupancy):
    jsonData["maxOccupancy"] = occupancy
    
def getMaxOccupancy(jsonData):
    return jsonData["maxOccupancy"]
    
def setMinOccupancy(jsonData, occupancy):
    jsonData["minOccupancy"] = occupancy

def getMinOccupancy(jsonData):
    return jsonData["minOccupancy"]
    
def setMeanOccupancy(jsonData, occupancy):
    jsonData["meanOccupancy"] = occupancy
    
def getMeanOccupancy(jsonData):
    return jsonData["meanOccupancy"]
    
def setMedianOccupancy(jsonData, occupancy):
    jsonData["medianOccupancy"] = occupancy

def getMedianOccupancy(jsonData):
    return jsonData["medianOccupancy"]

def setOccupancy(jsonData, occupancy):
    jsonData["occupancy"] = occupancy

def getOccupancy(jsonData):
    return jsonData["occupancy"]

def setMaxPower(jsonData, power):
    jsonData["maxPower"] = power

def getMaxPower(jsonData):
    return jsonData["maxPower"]

def setMinPower(jsonData, power):
    jsonData["minPower"] = power
    
def getMinPower(jsonData):
    return jsonData["minPower"]

    
    
    
    

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


'''
Created on Feb 11, 2015

@author: local
'''

import Message
from Defines import LAT, LON, ALT, TIME_ZONE_KEY
import numpy as np
import json


def setFirstDataMessageTimeStamp(jsonData, timeStamp):
    jsonData['firstDataMessageTimeStamp'] = timeStamp

def incrementMessageCount(jsonData):
    if "count" in jsonData:
       count = jsonData["count"]
       count = count+1
       jsonData["count"] = count
    else:
       jsonData["count"] = 1


def getMessageCount(jsonData):
    if not "count" in jsonData:
	return 0
    else:
	return jsonData["count"]

def setMinMaxPower(jsonData,minPower,maxPower):
      if not 'minPower' in jsonData:
         jsonData["minPower"] = minPower
         jsonData["maxPower"] = maxPower
      else:
         jsonData["minPower"] = np.minimum(jsonData["minPower"], minPower)
         jsonData["maxPower"] = np.maximum(jsonData["maxPower"], maxPower)

def addFreqRange(jsonData,freqRange):
     if not "sensorFreq" in jsonData:
          jsonData['sensorFreq'] = [freqRange]
     else:
         freqRanges = jsonData['sensorFreq']
         if not freqRange in freqRanges:
             freqRanges.append(freqRange)
         jsonData['sensorFreq'] = freqRanges

def getBandInfo(jsonData,bandName,fieldName):
     return jsonData["bandInfo"][bandName][fieldName]

def setBandInfo(jsonData,bandName,fieldName,info):
     if not "bandInfo" in jsonData:
	jsonData["bandInfo"] = {}
     if not bandName in jsonData["bandInfo"]:
	jsonData["bandInfo"][bandName] = {}
     jsonData["bandInfo"][bandName][fieldName] = info

def hasBandInfo(jsonData,bandName,fieldName):
     if not "bandInfo" in jsonData:
	return False
     elif not bandName in jsonData["bandInfo"]:
	return False
     elif not fieldName in jsonData["bandInfo"][bandName]:
	return False
     else:
	return True


def updateMaxBandOccupancy(jsonData,bandName,maxOccupancy):
     fieldName = "maxBandOccupancy"
     if not hasBandInfo(jsonData,bandName,fieldName):
	setBandInfo(jsonData,bandName,fieldName,maxOccupancy)
     else:
        newInfo =  np.maximum(getBandInfo(jsonData,bandName,fieldName),maxOccupancy)
	setBandInfo(jsonData,bandName,fieldName,newInfo)
     if not "maxOccupancy" in jsonData:
        jsonData["maxOccupancy"] = maxOccupancy
     else:
	jsonData["maxOccupancy"] = np.maximum(jsonData["maxOccupancy"],maxOccupancy)


def getMaxBandOccupancy(jsonData,bandName):
     fieldName = "maxBandOccupancy"
     if not hasBandInfo(jsonData,bandName,fieldName):
	return 0
     else:
	return getBandInfo(jsonData,bandName,fieldName)

def updateMinBandOccupancy(jsonData,bandName,minOccupancy):
     fieldName = "minBandOccupancy"
     if not hasBandInfo(jsonData,bandName,fieldName):
	setBandInfo(jsonData,bandName,fieldName,minOccupancy)
     else:
        newInfo =  np.minimum(getBandInfo(jsonData,bandName,fieldName),minOccupancy)
	setBandInfo(jsonData,bandName,fieldName,newInfo)
     if not "minOccupancy" in jsonData:
        jsonData["minOccupancy"] = minOccupancy
     else:
	jsonData["minOccupancy"] = np.minimum(jsonData["minOccupancy"],minOccupancy)

def getMinBandOccupancy(jsonData,bandName):
     fieldName = "minBandOccupancy"
     if not hasBandInfo(jsonData,bandName,fieldName):
	return 0
     else:
        return getBandInfo(jsonData,bandName,fieldName)

def updateOccupancySum(jsonData,bandName,occupancy):
     fieldName = "occupancySum"
     if not hasBandInfo(jsonData,bandName,fieldName):
	setBandInfo(jsonData,bandName,fieldName,occupancy)
     else:
        newInfo =  getBandInfo(jsonData,bandName,fieldName) + occupancy
	setBandInfo(jsonData,bandName,fieldName,newInfo)


def getMeanOccupancy(jsonData,bandName):
     if not hasBandInfo(jsonData,bandName,"occupancySum"):
	return 0
     else:
	occupancySum = getBandInfo(jsonData,bandName,"occupancySum")
	count = getBandInfo(jsonData,bandName,"bandMessageCount")
        if count == 0:
	   return 0
        else:
	   return occupancySum / count


def incrementBandCount(jsonData,bandName):
     fieldName = "bandMessageCount"
     if not hasBandInfo(jsonData,bandName,fieldName):
	setBandInfo(jsonData,bandName,fieldName,1)
     else:
        newInfo =  getBandInfo(jsonData,bandName,fieldName) + 1
	setBandInfo(jsonData,bandName,fieldName,newInfo)

def getBandCount(jsonData,bandName):
     fieldName = "bandMessageCount"
     if not hasBandInfo(jsonData,bandName,fieldName):
	return 0
     else:
	count = getBandInfo(jsonData,bandName,fieldName)
	return count

def setMessageTimeStampForBand(jsonData, bandName,timeStamp):
     fieldName = "firstMessageTimeStamp"
     if not hasBandInfo(jsonData,bandName,fieldName):
	setBandInfo(jsonData,bandName,fieldName,timeStamp)
	setBandInfo(jsonData,bandName,"lastMessageTimeStamp",timeStamp)
     else:
	setBandInfo(jsonData,bandName,"lastMessageTimeStamp",timeStamp)

def getFirstMessageTimeStampForBand(jsonData,bandName):
     fieldName = "firstMessageTimeStamp"
     if not hasBandInfo(jsonData,bandName,fieldName):
	return 0
     else:
        return getBandInfo(jsonData,bandName,fieldName)

def getLastMessageTimeStampForBand(jsonData,bandName):
     fieldName = "lastMessageTimeStamp"
     if not hasBandInfo(jsonData,bandName,fieldName):
	return 0
     else:
        return getBandInfo(jsonData,bandName,fieldName)



def setMessageTimeStamp(jsonData,timestamp):
    if not 'firstDataMessageTimeStamp' in jsonData:
       setFirstDataMessageTimeStamp( jsonData, timestamp)
       setLastDataMessageTimeStamp( jsonData, timestamp)
    else:
       setLastDataMessageTimeStamp(jsonData, timestamp)

def getFirstDataMessageTimeStamp(jsonData):
    return jsonData['firstDataMessageTimeStamp']


def getLastDataMessageTimeStamp(jsonData):
    return jsonData['lastDataMessageTimeStamp']


def setLastDataMessageTimeStamp(jsonData, timeStamp):
    jsonData['lastDataMessageTimeStamp'] = timeStamp


def getMinPower(jsonData):
    return jsonData["minPower"]


def getMaxPower(jsonData):
    return jsonData["maxPower"]


def setMinPower(jsonData, minPower):
    jsonData["minPower"] = minPower


def setMaxPower(jsonData, maxPower):
    jsonData["maxPower"] = maxPower


def getSensorId(jsonData):
    return Message.getSensorId(jsonData)


def getTimeZone(jsonData):
    return jsonData[TIME_ZONE_KEY]


def getLat(jsonData):
    return jsonData[LAT]


def getLon(jsonData):
    return jsonData[LON]


def getAlt(jsonData):
    return jsonData[ALT]


def getType(jsonData):
    return Message.getType(jsonData)


def clean(jsonData):
    del jsonData["minPower"]
    del jsonData["maxPower"]
    del jsonData["minOccupancy"]
    del jsonData["maxOccupancy"]
    del jsonData["lastDataMessageTimeStamp"]
    del jsonData["firstDataMessageTimeStamp"]
    del jsonData["count"]

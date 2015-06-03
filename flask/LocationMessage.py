'''
Created on Feb 11, 2015

@author: local
'''

import Message
from Defines import LAT,LON,ALT,TIME_ZONE_KEY

def setFirstDataMessageTimeStamp(jsonData,timeStamp):
    jsonData['firstDataMessageTimeStamp'] = timeStamp

def getFirstDataMessageTimeStamp(jsonData):
    return jsonData['firstDataMessageTimeStamp']

def getLastDataMessageTimeStamp(jsonData):
    return jsonData['lastDataMessageTimeStamp']

def setLastDataMessageTimeStamp(jsonData,timeStamp):
    jsonData['lastDataMessageTimeStamp'] = timeStamp
    
def setMaxOccupancy(jsonData,occupancy):
    jsonData["maxOccupancy"] = occupancy
    
def getMaxOccupancy(jsonData):
    return jsonData["maxOccupancy"]

def setMinOccupancy(jsonData,occupancy):
    jsonData["minOccupancy"] = occupancy

def getMinOccupancy(jsonData):
    return jsonData["minOccupancy"]

def getMinPower(jsonData):
    return jsonData["minPower"]

def getMaxPower(jsonData):
    return jsonData["maxPower"]

def setMinPower(jsonData,minPower):
    jsonData["minPower"] = minPower
    
def setMaxPower(jsonData,maxPower):
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
    
    


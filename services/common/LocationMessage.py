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


def setFirstDataMessageTimeStamp(jsonData, timeStamp):
    jsonData['firstDataMessageTimeStamp'] = timeStamp


def getFirstDataMessageTimeStamp(jsonData):
    return jsonData['firstDataMessageTimeStamp']


def getLastDataMessageTimeStamp(jsonData):
    return jsonData['lastDataMessageTimeStamp']


def setLastDataMessageTimeStamp(jsonData, timeStamp):
    jsonData['lastDataMessageTimeStamp'] = timeStamp


def setMaxOccupancy(jsonData, occupancy):
    jsonData["maxOccupancy"] = occupancy


def getMaxOccupancy(jsonData):
    return jsonData["maxOccupancy"]


def setMinOccupancy(jsonData, occupancy):
    jsonData["minOccupancy"] = occupancy


def getMinOccupancy(jsonData):
    return jsonData["minOccupancy"]


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

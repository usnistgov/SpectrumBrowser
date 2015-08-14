'''
Created on Feb 9, 2015

Common parts of the different messages are parsed here.

@author: local
'''

from Defines import TYPE
from Defines import SENSOR_ID


def getTime(jsonData):
    return jsonData["t"]

def getType(jsonData):
    return jsonData[TYPE]

def getSensorId(jsonData):
    return jsonData[SENSOR_ID]

def setInsertionTime(jsonData, insertionTime):
    jsonData["_localDbInsertionTime"] = insertionTime
    
def getInsertionTime(jsonData):
    return jsonData["_localDbInsertionTime"]
    

'''
Created on Jan 26, 2015

@author: mranga
'''
import time
import Accounts
import Config
import random
import SendMail
import util
import DbCollections
import msgutils
import SessionLock
import pymongo

from Sensor import Sensor
from Defines import SENSOR_ID
from Defines import SENSOR_KEY
from Defines import SENSOR_STATUS
from Defines import ENABLED
from Defines import DISABLED
from Defines import EXPIRE_TIME



def getAllSensors():
    sensors = []
    for sensor in DbCollections.getSensors().find() :
        sensorObj = Sensor(sensor)
        sensors.append(sensorObj.getSensor())
    return sensors

def getAllSensorIds():
    sensorIds = []
    for sensor in DbCollections.getSensors().find() :
        sensorIds.append(sensor[SENSOR_ID])

def checkSensorConfig(sensorConfig):
    if not SENSOR_ID in sensorConfig \
    or not SENSOR_KEY in sensorConfig \
    or not "sensorAdminEmail" in sensorConfig \
    or not "dataRetentionDurationMonths" in sensorConfig :
        return False, {"status":"NOK", "StatusMessage":"Missing required information"}
    else:
        return True, {"status":"OK"}

def addSensor(sensorConfig):
    status,msg = checkSensorConfig(sensorConfig)
    if not status:
        msg["sensors"] = getAllSensors()
        return msg
    sensorId = sensorConfig[SENSOR_ID]
    sensor = DbCollections.getSensors().find_one({SENSOR_ID:sensorId})
    if sensor != None:
        return {"status":"NOK", "StatusMessage":"Sensor already exists","sensors":getAllSensors()}
    else:
        sensorConfig[SENSOR_STATUS] = ENABLED
        DbCollections.getSensors().insert(sensorConfig)
        sensors = getAllSensors()
        dataPosts = DbCollections.getDataMessages(sensorId)
        dataPosts.ensure_index([('t',pymongo.ASCENDING),("seqNo",pymongo.ASCENDING)])
        return {"status":"OK", "sensors":sensors}
        
def getSystemMessage(sensorId):
    query = {SENSOR_ID:sensorId}
    record = DbCollections.getSensors().find_one(query)
    if record == None:
        return {"status":"NOK","StatusMessage":"Sensor not found"}
    else:
        systemMessage = record["systemMessage"]
        if systemMessage == None:
            return {"status":"NOK","StatusMessage":"System Message not found"}
        
def addDefaultOccupancyCalculationParameters(sensorId,jsonData):
    sensorRecord = DbCollections.getSensors().find_one({SENSOR_ID:sensorId})
    if sensorRecord == None:
        return {"status":"NOK","StatusMessage":"Sensor Not Found"}
    sensorRecord["defaultOccupancyCalculationParameters"]=jsonData
    recordId = sensorRecord["_id"]
    del sensorRecord["_id"]
    DbCollections.getSensors().update({"_id":recordId},sensorRecord,upsert=False)
    return {"status":"OK"}


def removeSensor(sensorId):
    SessionLock.acquire()
    try:
        userSessionCount = SessionLock.getUserSessionCount()
        if userSessionCount != 0 :
            return {"status":"NOK", "ErrorMessage":"Active user session detected"}
        sensor = DbCollections.getSensors().find_one({SENSOR_ID:sensorId})
        if sensor == None:
            return {"status":"NOK","StatusMessage":"Sensor Not Found","sensors":getAllSensors()}
        else:
            DbCollections.getSensors().remove(sensor)
            sensors = getAllSensors()
            return {"status":"OK", "sensors":sensors}
    finally:
        SessionLock.release()
    
def getSensors():
    sensors = getAllSensors()
    return {"status":"OK","sensors":sensors}

def printSensors():
    import json
    sensors = getAllSensors()
    for sensor in sensors:
        print json.dumps(sensor,indent=4)

def getSensor(sensorId):
    sensor = DbCollections.getSensors().find_one({SENSOR_ID:sensorId})
    if sensor == None:
        return None
    else:
        return Sensor(sensor).getSensor()
    
def getSensorObj(sensorId):
    sensor = DbCollections.getSensors().find_one({SENSOR_ID:sensorId})
    if sensor == None:
        return None
    else:
        return Sensor(sensor)


        
def purgeSensor(sensorId):
    SessionLock.acquire()
    try :
        userSessionCount = SessionLock.getUserSessionCount()
        if userSessionCount != 0 :
            return {"status":"NOK", "ErrorMessage":"Active user session detected"}
        DbCollections.getSensors().remove({SENSOR_ID:sensorId})
        systemMessages = DbCollections.getSystemMessages().find({SENSOR_ID:sensorId})
        # The system message can contain cal data.
        for systemMessage in systemMessages:
            msgutils.removeData(systemMessage)
        DbCollections.getSystemMessages().remove({SENSOR_ID:sensorId})
        dataMessages = DbCollections.getDataMessages(sensorId).find({SENSOR_ID:sensorId})
        # remove data associated with data messages.
        for dataMessage in dataMessages:
            msgutils.removeData(dataMessage)   
        DbCollections.getDataMessages(sensorId).remove({SENSOR_ID:sensorId})
        DbCollections.dropDataMessages(sensorId)
        # Location messages contain no associated data.
        DbCollections.getLocationMessages().remove({SENSOR_ID:sensorId})
        sensors = getAllSensors()
        return {"status":"OK", "sensors":sensors}
    finally:
        SessionLock.release()

def toggleSensorStatus(sensorId):
    sensor = DbCollections.getSensors().find_one({SENSOR_ID:sensorId})
    currentStatus = sensor[SENSOR_STATUS]
    if currentStatus == DISABLED:
        newStatus = ENABLED
    else:
        newStatus = DISABLED
    DbCollections.getSensors().update({"_id":sensor["_id"]}, {"$set":{SENSOR_STATUS:newStatus}},upsert=False)
    sensors = getAllSensors()
    return {"status":"OK","sensors":sensors}


def updateSensor(sensorConfigData):
    status,msg = checkSensorConfig(sensorConfigData)
    if not status:
        msg["sensors"] = getAllSensors()
        return msg
    sensorId = sensorConfigData[SENSOR_ID]
    DbCollections.getSensors().remove({SENSOR_ID:sensorId})
    DbCollections.getSensors().insert(sensorConfigData)
    sensors = getAllSensors()
    return {"status":"OK", "sensors":sensors}
    
def startSensorDbScanner():
    tempSensors = DbCollections.getTempSensorsCollection()
    Accounts.removeExpiredRows(tempSensors)
    
    

    
        
        

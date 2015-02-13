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
from Sensor import Sensor
from Defines import SENSOR_ID
from Defines import SENSOR_KEY
from Defines import SENSOR_STATUS
from Defines import ENABLED
from Defines import DISABLED

def getAllSensors():
    sensors = []
    for sensor in DbCollections.getSensors().find() :
        sensorObj = Sensor(sensor)
        sensors.append(sensorObj.getSensor())
    return sensors

def checkSensorConfig(sensorConfig):
    if not SENSOR_ID in sensorConfig \
    or not SENSOR_KEY in sensorConfig \
    or not "sensorAdminEmail" in sensorConfig \
    or not "dataRetentionDurationMonths" in sensorConfig :
        return False, {"Status":"NOK", "StatusMessage":"Missing required information"}
    else:
        return True, {"Status":"OK"}

def addSensor(sensorConfig):
    status,msg = checkSensorConfig(sensorConfig)
    if not status:
        msg["sensors"] = getAllSensors()
        return msg
    sensorId = sensorConfig[SENSOR_ID]
    sensor = DbCollections.getSensors().find_one({SENSOR_ID:sensorId})
    if sensor != None:
        return {"Status":"NOK", "StatusMessage":"Sensor already exists","sensors":getAllSensors()}
    else:
        sensorConfig[SENSOR_STATUS] = ENABLED
        DbCollections.getSensors().insert(sensorConfig)
        sensors = getAllSensors()
        return {"Status":"OK", "sensors":sensors}
        
def addTempSensor(sensorId,sensorKey,sensorAdminEmail,systemMessage):
    sensor = DbCollections.getSensors().find_one({SENSOR_ID:sensorId})
    tempSensor = DbCollections.getTempSensorsCollection().find_one({SENSOR_ID:sensorId})
    if sensor != None:
        return {"Status":"NOK", "StatusMessage":"Sensor already exists"}
    elif tempSensor != None:
        return {"Status":"NOK", "StatusMessage":"Sensor add request already exists"}
    else:
        record = {SENSOR_ID:sensorId, SENSOR_KEY:sensorKey, "activated": False, "systemMessage":systemMessage }
        record["expireTime"] = time.time() + Config.getSensorConfigExpiryTimeHours()*60*60
        record["_token"] = str(random.randint(1000000))
        record["activated"] = False
        DbCollections.getTempSensorsCollection().insert(record)
        url = util.generateUrl(Config.getAccessProtocol(), Config.getHostName(), Config.getPublicPort())
        url = url + "/admin/approveSensor/"+ record["token"]
        emailMessage = "A user has requested to add a sensor. Please visit admin page and click here to add sensor " + url
        SendMail.sendMail(emailMessage,Accounts.getAdminAccount(),Accounts.getAdminAccount())
        
        
def approveSensor(tokenId):
    sensor = DbCollections.getTempSensorsCollection().find({"_token":tokenId})
    if ( sensor == None):
        return {"Status":"NOK","StatusMessage":"Sensor activation request not found"}
    else:
        DbCollections.getTempSensorsCollection().remove(sensor)
        del sensor["_id"]
        del sensor["_token"]
        DbCollections.getSensors().insert(sensor)             

def getSystemMessage(sensorId):
    query = {SENSOR_ID:sensorId}
    record = DbCollections.getSensors().find_one(query)
    if record == None:
        return {"Status":"NOK","StatusMessage":"Sensor not found"}
    else:
        systemMessage = record["systemMessage"]
        if systemMessage == None:
            return {"Status":"NOK","StatusMessage":"System Message not found"}
        
def addDefaultOccupancyCalculationParameters(sensorId,jsonData):
    sensorRecord = DbCollections.getSensors().find_one({SENSOR_ID:sensorId})
    if sensorRecord == None:
        return {"Status":"NOK","StatusMessage":"Sensor Not Found"}
    sensorRecord["defaultOccupancyCalculationParameters"]=jsonData
    recordId = sensorRecord["_id"]
    del sensorRecord["_id"]
    DbCollections.getSensors().update({"_id":recordId},sensorRecord,upsert=False)
    return {"Status":"OK"}


def removeSensor(sensorId):
    sensor = DbCollections.getSensors().find_one({SENSOR_ID:sensorId})
    if sensor == None:
        return {"Status":"NOK","StatusMessage":"Sensor Not Found","sensors":getAllSensors()}
    else:
        DbCollections.getSensors().remove(sensor)
        sensors = getAllSensors()
        return {"Status":"OK", "sensors":sensors}
    
def getSensors():
    sensors = getAllSensors()
    return {"Status":"OK","sensors":sensors}

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
    DbCollections.getSensors().remove({SENSOR_ID:sensorId})
    systemMessages = DbCollections.getSystemMessages().find({SENSOR_ID:sensorId})
    # The system message can contain cal data.
    for systemMessage in systemMessages:
        msgutils.removeData(systemMessage)
    DbCollections.getSystemMessages().remove({SENSOR_ID:sensorId})
    dataMessages = DbCollections.getDataMessages().find({SENSOR_ID:sensorId})
    # remove data associated with data messages.
    for dataMessage in dataMessages:
        msgutils.removeData(dataMessage)   
    DbCollections.getDataMessages().remove({SENSOR_ID:sensorId})
    # Location messages contain no associated data.
    DbCollections.getLocationMessages().remove({SENSOR_ID:sensorId})
    sensors = getAllSensors()
    return {"Status":"OK", "sensors":sensors}

def toggleSensorStatus(sensorId):
    sensor = DbCollections.getSensors().find_one({SENSOR_ID:sensorId})
    currentStatus = sensor[SENSOR_STATUS]
    if currentStatus == DISABLED:
        newStatus = ENABLED
    else:
        newStatus = DISABLED
    DbCollections.getSensors().update({"_id":sensor["_id"]}, {"$set":{SENSOR_STATUS:newStatus}},upsert=False)
    sensors = getAllSensors()
    return {"Status":"OK","sensors":sensors}


def updateSensor(sensorConfigData):
    status,msg = checkSensorConfig(sensorConfigData)
    if not status:
        msg["sensors"] = getAllSensors()
        return msg
    sensorId = sensorConfigData[SENSOR_ID]
    DbCollections.getSensors().remove({SENSOR_ID:sensorId})
    DbCollections.getSensors().insert(sensorConfigData)
    sensors = getAllSensors()
    return {"Status":"OK", "sensors":sensors}
    
def startSensorDbScanner():
    tempSensors = DbCollections.getTempSensorsCollection()
    Accounts.removeExpiredRows(tempSensors)
    
    

    
        
        

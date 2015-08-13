'''
Created on Feb 11, 2015

@author: local
'''
import DbCollections
import DataMessage
import LocationMessage
import Message
import SensorDb
from Defines import SECONDS_PER_DAY, SENSOR_ID, SWEPT_FREQUENCY, ENABLED
import pymongo
import SessionLock
import time
import msgutils
import numpy as np

def runGarbageCollector(sensorId):
    SessionLock.acquire()
    try :
        userCount = SessionLock.getUserSessionCount()
        if userCount != 0:
            return {"status":"NOK", "ErrorMessage":"Active user session detected"}
        sensorObj = SensorDb.getSensorObj(sensorId)
        if sensorObj == None:
            return {"status":"NOK", "ErrorMessage":"Sensor Not found"}
        if sensorObj.getSensorStatus() == ENABLED:
            return {"status":"NOK", "ErrorMessage":"Sensor is ENABLED -- DISABLE it first"}
            
        dataRetentionDuration = sensorObj.getSensorDataRetentionDurationMonths()
        dataRetentionTime = dataRetentionDuration * 30 * SECONDS_PER_DAY
        cur = DbCollections.getDataMessages(sensorId).find({SENSOR_ID:sensorId})
        dataMessages = cur.sort('t', pymongo.ASCENDING)
        currentTime = time.time()
        locationMessage = None
        for msg in dataMessages:
            insertionTime = Message.getInsertionTime(msg)
            if currentTime - dataRetentionTime >= insertionTime:
                DbCollections.getDataMessages(sensorId).remove(msg)
            else:
                break
            
        # Now redo our book keeping summary fields.
        cur = DbCollections.getDataMessages(sensorId).find({SENSOR_ID:sensorId})
        dataMessages = cur.sort('t', pymongo.ASCENDING)
        locationMessages = DbCollections.getLocationMessages().find({SENSOR_ID:sensorId})
        for locationMessage in locationMessages:
            LocationMessage.clean(locationMessage)
            DbCollections.getLocationMessages().update({"_id":locationMessage["_id"]}, {"$set":locationMessage}, upsert=False)
        
        for jsonData in dataMessages:
            minPower = DataMessage.getMinPower(jsonData)
            maxPower = DataMessage.getMaxPower(jsonData)
            lastLocationPost = msgutils.getLocationMessage(jsonData)
            if not 'firstDataMessageTimeStamp' in lastLocationPost :
                LocationMessage.setFirstDataMessageTimeStamp(lastLocationPost, Message.getTime(jsonData))
                LocationMessage.setLastDataMessageTimeStamp(lastLocationPost, Message.getTime(jsonData))
            else :
                LocationMessage.setLastDataMessageTimeStamp(lastLocationPost, Message.getTime(jsonData))
            if not 'minPower' in lastLocationPost:
                lastLocationPost["minPower"] = minPower
                lastLocationPost["maxPower"] = maxPower
            else:
                lastLocationPost["minPower"] = np.minimum(lastLocationPost["minPower"], minPower)
                lastLocationPost["maxPower"] = np.maximum(lastLocationPost["maxPower"], maxPower)
            if not "maxOccupancy" in lastLocationPost:
                if jsonData["mType"] == SWEPT_FREQUENCY:
                    lastLocationPost["maxOccupancy"] = jsonData["occupancy"]
                    lastLocationPost["minOccupancy"] = jsonData["occupancy"]
                else:
                    lastLocationPost["maxOccupancy"] = jsonData["maxOccupancy"]
                    lastLocationPost["minOccupancy"] = jsonData["minOccupancy"]
            else:
                if DataMessage.getMeasurementType(jsonData) == SWEPT_FREQUENCY:
                    lastLocationPost["maxOccupancy"] = np.maximum(lastLocationPost["maxOccupancy"], jsonData["occupancy"])
                    lastLocationPost["minOccupancy"] = np.minimum(lastLocationPost["minOccupancy"], jsonData["occupancy"])
                else:
                    lastLocationPost["maxOccupancy"] = np.maximum(lastLocationPost["maxOccupancy"], jsonData["maxOccupancy"])
                    lastLocationPost["minOccupancy"] = np.minimum(lastLocationPost["minOccupancy"], jsonData["minOccupancy"])
            DbCollections.getLocationMessages().update({"_id":lastLocationPost["_id"]}, {"$set":lastLocationPost}, upsert=False)

        return {"status":"OK", "sensors":SensorDb.getAllSensors()}
    finally:
        SessionLock.release()

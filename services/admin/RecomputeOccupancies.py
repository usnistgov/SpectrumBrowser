import SessionLock
import DbCollections
import DataMessage
import msgutils
import numpy as np
import util
import SensorDb
from Defines import SENSOR_ID, SWEPT_FREQUENCY


def recomputeOccupancies(sensorId):
    if SessionLock.isAcquired():
        return {"status": "NOK",
                "StatusMessage": "Session is locked. Try again later."}
    SessionLock.acquire()
    try:
        dataMessages = DbCollections.getDataMessages(sensorId).find(
            {SENSOR_ID: sensorId})
        if dataMessages == None:
            return {"status": "OK", "StatusMessage": "No Data Found"}
        for jsonData in dataMessages:
            if DataMessage.resetThreshold(jsonData):
                DbCollections.getDataMessages(sensorId).update(
                    {"_id": jsonData["_id"]}, {"$set": jsonData},
                    upsert=False)
                lastLocationPost = msgutils.getLocationMessage(jsonData)
                if not "maxOccupancy" in lastLocationPost:
                    if jsonData["mType"] == SWEPT_FREQUENCY:
                        lastLocationPost["maxOccupancy"] = jsonData[
                            "occupancy"]
                        lastLocationPost["minOccupancy"] = jsonData[
                            "occupancy"]
                    else:
                        lastLocationPost["maxOccupancy"] = jsonData[
                            "maxOccupancy"]
                        lastLocationPost["minOccupancy"] = jsonData[
                            "minOccupancy"]
                else:
                    if DataMessage.getMeasurementType(
                            jsonData) == SWEPT_FREQUENCY:
                        lastLocationPost["maxOccupancy"] = np.maximum(
                            lastLocationPost["maxOccupancy"],
                            jsonData["occupancy"])
                        lastLocationPost["minOccupancy"] = np.minimum(
                            lastLocationPost["minOccupancy"],
                            jsonData["occupancy"])
                    else:
                        lastLocationPost["maxOccupancy"] = np.maximum(
                            lastLocationPost["maxOccupancy"],
                            jsonData["maxOccupancy"])
                        lastLocationPost["minOccupancy"] = np.minimum(
                            lastLocationPost["minOccupancy"],
                            jsonData["minOccupancy"])
                DbCollections.getLocationMessages().update(
                    {"_id": lastLocationPost["_id"]},
                    {"$set": lastLocationPost},
                    upsert=False)
            else:
                util.debugPrint("Threshold is unchanged -- not resetting")
        return {"status": "OK", "sensors": SensorDb.getAllSensors()}
    finally:
        SessionLock.release()


def resetNoiseFloor(sensorId, noiseFloor):
    if SessionLock.isAcquired():
        return {"status": "NOK",
                "StatusMessage": "Session is locked. Try again later."}
    SessionLock.acquire()
    try:
        dataMessages = DbCollections.getDataMessages(sensorId).find(
            {SENSOR_ID: sensorId})
        if dataMessages == None:
            return {"status": "OK", "StatusMessage": "No Data Found"}
        SessionLock.release()
        for jsonData in dataMessages:
            DbCollections.getDataMessages(sensorId).update(
                {"_id": jsonData["_id"]}, {"$set": jsonData},
                upsert=False)
    finally:
        SessionLock.release()
    return {"status": "OK", "sensors": SensorDb.getAllSensors()}

#! /usr/local/bin/python2.7
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
Created on Jan 26, 2015

@author: mranga
'''
import Accounts
import DbCollections
import msgutils
import SessionLock
import pymongo
import authentication
import argparse
import os
import sys
import signal
import util
import socket
import traceback
import json
from DataStreamSharedState import MemCache
import Config

from Sensor import Sensor
from Defines import SENSOR_ID
from Defines import SENSOR_KEY
from Defines import SENSOR_STATUS
from Defines import ENABLED
from Defines import DISABLED
from Defines import STATUS
from Defines import OK
from Defines import NOK
from Defines import ERROR_MESSAGE
from Defines import IS_STREAMING_ENABLED
from Defines import SENSOR_THRESHOLDS
from Defines import PURGING


def getAllSensors():
    sensors = []
    for sensor in DbCollections.getSensors().find():
        sensorObj = Sensor(sensor)
        sensors.append(sensorObj.getSensor())
    return sensors


def getAllSensorIds():
    sensorIds = []
    for sensor in DbCollections.getSensors().find():
        sensorIds.append(sensor[SENSOR_ID])


def checkSensorConfig(sensorConfig):
    minTime = Config.getMinStreamingInterArrivalTimeSeconds()
    sensorObj = Sensor(sensorConfig)
    if sensorObj.isStreamingEnabled() and sensorObj.getStreamingSecondsPerFrame() > 0 and \
       sensorObj.getStreamingSecondsPerFrame() < minTime:
        return False, {STATUS: "NOK",
                       "StatusMessage":
                       "streaming interarrival time is too small"}
    if SENSOR_ID not in sensorConfig \
       or SENSOR_KEY not in sensorConfig \
       or "sensorAdminEmail" not in sensorConfig \
       or "dataRetentionDurationMonths" not in sensorConfig:
        return False, {STATUS: "NOK",
                       "StatusMessage": "Missing required information"}
    else:
        return True, {STATUS: "OK"}


def addSensor(sensorConfig):
    status, msg = checkSensorConfig(sensorConfig)
    if not status:
        msg["sensors"] = getAllSensors()
        return msg
    sensorId = sensorConfig[SENSOR_ID]
    sensor = DbCollections.getSensors().find_one({SENSOR_ID: sensorId})
    if sensor is not None:
        return {STATUS: "NOK",
                "StatusMessage": "Sensor already exists",
                "sensors": getAllSensors()}
    else:
        sensorConfig[SENSOR_STATUS] = ENABLED
        DbCollections.getSensors().insert(sensorConfig)
        dataPosts = DbCollections.getDataMessages(sensorId)
        dataPosts.create_index([('t', pymongo.ASCENDING)])
        sensors = getAllSensors()
        return {STATUS: "OK", "sensors": sensors}


def getSystemMessage(sensorId):
    query = {SENSOR_ID: sensorId}
    record = DbCollections.getSensors().find_one(query)
    if record is None:
        return {STATUS: "NOK", "StatusMessage": "Sensor not found"}
    else:
        systemMessage = record["systemMessage"]
        if systemMessage is None:
            return {STATUS: "NOK", "StatusMessage": "System Message not found"}


def addDefaultOccupancyCalculationParameters(sensorId, jsonData):
    sensorRecord = DbCollections.getSensors().find_one({SENSOR_ID: sensorId})
    if sensorRecord is None:
        return {STATUS: "NOK", "StatusMessage": "Sensor Not Found"}
    sensorRecord["defaultOccupancyCalculationParameters"] = jsonData
    recordId = sensorRecord["_id"]
    del sensorRecord["_id"]
    DbCollections.getSensors().update({"_id": recordId},
                                      sensorRecord,
                                      upsert=False)
    return {STATUS: "OK"}


def notifyConfigChange(sensorId):
    memCache = MemCache()
    port = memCache.getSensorArmPort(sensorId)
    soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    soc.sendto(
        json.dumps({"sensorId": sensorId,
                    "command": "retune"}), ("localhost", port))
    soc.close()


def activateBand(sensorId, bandName):
    query = {SENSOR_ID: sensorId}
    record = DbCollections.getSensors().find_one(query)
    if record is None:
        return {STATUS: "NOK", "StatusMessage": "Sensor not found"}
    if bandName not in record[SENSOR_THRESHOLDS]:
        return {STATUS: "NOK", "StatusMessage": "Band not found"}
    for threshold in record[SENSOR_THRESHOLDS].values():
        threshold["active"] = False
    threshold = record[SENSOR_THRESHOLDS][bandName]
    threshold["active"] = True
    del record["_id"]
    DbCollections.getSensors().update({SENSOR_ID: sensorId},
                                      record,
                                      upsert=False)
    return {STATUS: "OK"}


def getBand(sensorId, bandName):
    query = {SENSOR_ID: sensorId}
    record = DbCollections.getSensors().find_one(query)
    if record is None:
        return None
    if bandName not in record[SENSOR_THRESHOLDS]:
        return None
    return record[SENSOR_THRESHOLDS][bandName]


def removeAllSensors():
    DbCollections.getSensors().drop()


def removeSensor(sensorId):
    """
    Remove a sensor.
    """
    SessionLock.acquire()
    try:
        userSessionCount = SessionLock.getUserSessionCount()
        if userSessionCount != 0:
            return {STATUS: "NOK",
                    "StatusMessage": "Active user session detected"}
        sensor = DbCollections.getSensors().find_one({SENSOR_ID: sensorId})
        if sensor is None:
            return {STATUS: "NOK",
                    "StatusMessage": "Sensor Not Found",
                    "sensors": getAllSensors()}
        else:
            DbCollections.getSensors().remove(sensor)
            sensors = getAllSensors()
            return {STATUS: "OK", "sensors": sensors}
    finally:
        SessionLock.release()


def getSensors(getMessageDates=False):
    """
    Get the sensor configurations and optionally get the final messages associated with the sensors.
    """
    sensors = getAllSensors()
    if not getMessageDates:
        for sensor in sensors:
            if "messageDates" in sensor:
                del sensor["messageDates"]
            if "messageJsons" in sensor:
                del sensor["messageJsons"]
            if "messageData" in sensor:
                del sensor["messageData"]
    return {STATUS: "OK", "sensors": sensors}


def printSensors():
    import json
    sensors = getAllSensors()
    for sensor in sensors:
        print json.dumps(sensor, indent=4)


def getSensor(sensorId):
    sensor = DbCollections.getSensors().find_one({SENSOR_ID: sensorId})
    if sensor is None:
        return None
    else:
        return Sensor(sensor).getSensor()


def getSensorObj(sensorId):
    sensor = DbCollections.getSensors().find_one({SENSOR_ID: sensorId})
    if sensor is None:
        return None
    else:
        return Sensor(sensor)


def getSensorConfig(sensorId):
    util.debugPrint("SensorDb:getSensorConfig: " + sensorId)
    sensor = DbCollections.getSensors().find_one({SENSOR_ID: sensorId})
    if sensor is None:
        return {STATUS: NOK, ERROR_MESSAGE: "Sensor not found " + sensorId}
    else:
        del sensor[SENSOR_KEY]
        del sensor["_id"]
        if "messageDates" in sensor:
            del sensor["messageDates"]
        if "messageJsons" in sensor:
            del sensor["messageJsons"]
        if "messageData" in sensor:
            del sensor["messageData"]
        return {STATUS: OK, "sensorConfig": sensor}


def markSensorForPurge(sensorId):
    sensor = getSensorObj(sensorId)
    if sensor is None:
        return {STATUS:"NOK", "ErrorMessage":"Sensor " + sensorId + " not found. "}
    if sensor.getSensorStatus() == ENABLED:
        return {STATUS: "NOK",
                "ErrorMessage":"Sensor is ENABLED - please disable it."}
    else:
        retval = setSensorStatus(sensorId, PURGING)
    sensors = getAllSensors()
    if retval:
        status = "OK"
    else:
        status = "NOK"
    return {STATUS: status, "sensors": sensors}


def purgeSensor(sensor):
    try:
        sensorId = sensor.getSensorId()
        util.debugPrint("SensorDb::purgeSensor " + sensor.getSensorId())
        userSessionCount = SessionLock.getUserSessionCount()
        sensor = getSensorObj(sensorId)
        if sensor.getSensorStatus() == "ENABLED":
            return
        restartSensor(sensorId)
        systemMessages = DbCollections.getSystemMessages().find(
            {SENSOR_ID: sensorId})
        # The system message can contain cal data.
        for systemMessage in systemMessages:
            msgutils.removeData(systemMessage)
        DbCollections.getSystemMessages().remove({SENSOR_ID: sensorId})
        dataMessages = DbCollections.getDataMessages(sensorId).find(
            {SENSOR_ID: sensorId})
        # remove data associated with data messages.
        for dataMessage in dataMessages:
            msgutils.removeData(dataMessage)
        DbCollections.getDataMessages(sensorId).remove({SENSOR_ID: sensorId})
        DbCollections.dropDataMessages(sensorId)
        # remove the capture events.
        DbCollections.getCaptureEventDb(sensorId).remove({SENSOR_ID: sensorId})
        # Location messages contain no associated data.
        DbCollections.getLocationMessages().remove({SENSOR_ID: sensorId})
        # Clean the sensor.
        sensor.cleanSensorStats()
        for dataMessage in DbCollections.getUnprocessedDataMessages(sensorId).find():
            msgutils.removeData(dataMessage)
        DbCollections.dropUnprocessedDataMessages(sensorId)
        setSensorStatus(sensorId, ENABLED)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())


def deleteSensor(sensorId):
    try:
        systemMessageCount = DbCollections.getSystemMessages().find(
            {SENSOR_ID: sensorId}).count()
        dataMessageCount = DbCollections.getDataMessages(sensorId).count()
        locationMessageCount = DbCollections.getLocationMessages().find(
            {SENSOR_ID: sensorId}).count()
        if systemMessageCount != 0 or dataMessageCount != 0 or locationMessageCount != 0:
            return {STATUS: "NOK",
                    "ErrorMessage": "Please purge sensor before deleting it."}

        DbCollections.getSensors().remove({SENSOR_ID: sensorId})
        sensors = getAllSensors()
        return {STATUS: "OK", "sensors": sensors}
    finally:
        SessionLock.release()


def toggleSensorStatus(sensorId):
    sensor = DbCollections.getSensors().find_one({SENSOR_ID: sensorId})
    if sensor is None:
        return {STATUS: "NOK", "ErrorMessage": "Sensor Not Found"}
    currentStatus = sensor[SENSOR_STATUS]
    status = "OK"
    errorMessage = None
    if currentStatus != ENABLED and currentStatus != DISABLED:
        status = "NOK"
        errorMessage = "Cannot toggle state -- sensor state is  " + currentStatus
    elif currentStatus == DISABLED:
        newStatus = ENABLED
    else:
        newStatus = DISABLED
        restartSensor(sensorId)
    if status == "OK":
        DbCollections.getSensors().update({"_id": sensor["_id"]},
                                          {"$set": {SENSOR_STATUS: newStatus}},
                                          upsert=False)
    sensors = getAllSensors()
    retval = {STATUS: status, "sensors": sensors}
    if errorMessage is not None:
        retval["ErrorMessage"] = errorMessage
    return retval


def setSensorStatus(sensorId, newStatus):
    sensor = DbCollections.getSensors().find_one({SENSOR_ID: sensorId})
    if sensor is None:
        return False
    DbCollections.getSensors().update({"_id": sensor["_id"]},
                                      {"$set": {SENSOR_STATUS: newStatus}},
                                      upsert=False)
    return True


def postError(sensorId, errorStatus):
    sensor = DbCollections.getSensors().find_one({SENSOR_ID: sensorId})
    if "SensorKey" not in errorStatus:
        return {STATUS: "NOK",
                "ErrorMessage":
                "Authentication failure - sensor key not provided"}
    if sensor is None:
        return {STATUS: "NOK", "ErrorMessage": "Sensor not found"}
    if not authentication.authenticateSensor(sensorId,
                                             errorStatus[SENSOR_KEY]):
        return {STATUS:"NOK", "ErrorMessage":"Authentication failure"}
    DbCollections.getSensors().update(
        {"_id": sensor["_id"]},
        {"$set": {"SensorError": errorStatus["ErrorMessage"]}},
        upsert=False)
    return {STATUS: OK}


def restartSensor(sensorId):
    memCache = MemCache()
    pid = memCache.getStreamingServerPid(sensorId)
    if pid != -1:
        try:
            util.debugPrint("restartSensor: sensorId " + sensorId + " pid " +
                            str(pid) + " sending sigint")
            os.kill(pid, signal.SIGINT)
        except:
            util.errorPrint("restartSensor: Pid " + str(pid) + " not found")
    else:
        util.debugPrint("restartSensor: pid not found")


def updateSensor(sensorConfigData, restart=True, getsensors=True):
    status, msg = checkSensorConfig(sensorConfigData)
    if not status:
        msg["sensors"] = getAllSensors()
        return msg
    sensorId = sensorConfigData[SENSOR_ID]
    DbCollections.getSensors().update({"SensorID": sensorId},
                                      {"$set": sensorConfigData},
                                      upsert=False)
    if getSensors:
        sensors = getAllSensors()
        if sensorConfigData[IS_STREAMING_ENABLED] and restart:
            restartSensor(sensorId)
        return {STATUS: "OK", "sensors": sensors}
    else:
        return {STATUS: "OK"}


def startSensorDbScanner():
    tempSensors = DbCollections.getTempSensorsCollection()
    Accounts.removeExpiredRows(tempSensors)


def add_sensors(filename):
    with open(filename, 'r') as f:
        data = f.read()
    sensors = eval(data)
    for sensor in sensors:
        addSensor(sensor)


# Note this is for manual deletion of all sensors for testing starting from scratch.
def deleteAllSensors():
    DbCollections.getSensors().remove({})

# Self initialization scaffolding code.
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument('action', default="init", help="init (default)")
    parser.add_argument('-f', help='sensors file')
    args = parser.parse_args()
    action = args.action
    if args.action == "init" or args.action is None:
        sensorsFile = args.f
        if sensorsFile is None:
            parser.error("Please specify sensors file")
        deleteAllSensors()
        add_sensors(sensorsFile)
    else:
        parser.error("Unknown option " + args.action)

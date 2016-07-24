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

import SessionLock
import DbCollections
import DataMessage
import SensorDb
import LocationMessage
import msgutils
import util
import sys
import json
import traceback
from Defines import SENSOR_ID, FFT_POWER
from Defines import ENABLED, RECOMPUTING, PURGING


def recomputeOccupancies(sensorId):
    sensorObj = SensorDb.getSensorObj(sensorId)
    if sensorObj.getSensorStatus() == PURGING:
        return {"status": "NOK", "ErrorMessage":"Sensor is PURGING"}
    elif sensorObj.getSensorStatus() == RECOMPUTING:
        return {"status": "NOK", "ErrorMessage":"Sensor is RECOMPUTING"}
    else:
        SensorDb.setSensorStatus(sensorId,RECOMPUTING)

    return {"status": "OK", "sensors": SensorDb.getAllSensors()}


def recomputeOccupanciesWorker(sensorId):
    # Clean out the summary stats.
    util.debugPrint("recomputeOccupanciesWorker " + sensorId)
    sensorObj = SensorDb.getSensorObj(sensorId)
    if sensorObj is None:
        return
    try:
        sensorObj.cleanSensorStats()
        cur = DbCollections.getDataMessages(sensorId).find()
        if cur is None or cur.count() == 0:
            return
        locationMessages = DbCollections.getLocationMessages().find(
            {SENSOR_ID: sensorId})
        for locationMessage in locationMessages:
            lid = locationMessage["_id"]
            LocationMessage.clean(locationMessage)
            util.debugPrint("Location Message " + json.dumps(locationMessage, indent=4))
            DbCollections.getLocationMessages().update(
                {"_id": lid}, {"$set": locationMessage},
                upsert=False)

        for jsonData in cur:
            freqRange = DataMessage.getFreqRange(jsonData)
            # TODO -- recompute the occupancies. for data message.
            DataMessage.resetThreshold(jsonData)
            dataMsgId = jsonData["_id"]
            del jsonData["_id"]
            DbCollections.getDataMessages(sensorId).update({"_id":dataMsgId},{"$set":jsonData},upsert=False)
            minPower = DataMessage.getMinPower(jsonData)
            maxPower = DataMessage.getMaxPower(jsonData)
            lastLocationPost = msgutils.getLocationMessage(jsonData)
            if DataMessage.getMeasurementType(jsonData) == FFT_POWER:
                minOccupancy = DataMessage.getMinOccupancy(jsonData)
                maxOccupancy = DataMessage.getMaxOccupancy(jsonData)
                meanOccupancy = DataMessage.getMeanOccupancy(jsonData)
                sensorObj.updateMinOccupancy(freqRange, minOccupancy)
                sensorObj.updateMaxOccupancy(freqRange, maxOccupancy)
                sensorObj.updateOccupancyCount(freqRange, meanOccupancy)
                LocationMessage.updateMaxBandOccupancy(lastLocationPost, freqRange,
                                                       maxOccupancy)
                LocationMessage.updateMinBandOccupancy(lastLocationPost, freqRange,
                                                       minOccupancy)
                LocationMessage.updateOccupancySum(lastLocationPost, freqRange,
                                                   meanOccupancy)
            else:
                occupancy = DataMessage.getOccupancy(jsonData)
                sensorObj.updateMinOccupancy(freqRange, occupancy)
                sensorObj.updateMaxOccupancy(freqRange, occupancy)
                sensorObj.updateOccupancyCount(freqRange, occupancy)
                LocationMessage.updateMaxBandOccupancy(lastLocationPost, freqRange,
                                                       occupancy)
                LocationMessage.updateMinBandOccupancy(lastLocationPost, freqRange,
                                                       occupancy)
                LocationMessage.updateOccupancySum(lastLocationPost, freqRange,
                                                   occupancy)
            DbCollections.getLocationMessages().update(
                {"_id": lastLocationPost["_id"]}, {"$set": lastLocationPost},
                upsert=False)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
    finally:
        SensorDb.setSensorStatus(sensorId,ENABLED)


def resetNoiseFloor(sensorId, noiseFloor):
    if SessionLock.isAcquired():
        return {"status": "NOK",
                "StatusMessage": "Session is locked. Try again later."}
    SessionLock.acquire()
    try:
        dataMessages = DbCollections.getDataMessages(sensorId).find(
            {SENSOR_ID: sensorId})
        if dataMessages is None:
            return {"status": "OK", "StatusMessage": "No Data Found"}
        SessionLock.release()
        for jsonData in dataMessages:
            DbCollections.getDataMessages(sensorId).update(
                {"_id": jsonData["_id"]}, {"$set": jsonData},
                upsert=False)
    finally:
        SessionLock.release()
    return {"status": "OK", "sensors": SensorDb.getAllSensors()}

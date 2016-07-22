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
import Message
import msgutils
import util
import json
from Defines import SENSOR_ID, FFT_POWER


def recomputeOccupancies(sensorId):
    if SessionLock.isAcquired():
        return {"status": "NOK",
                "StatusMessage": "Session is locked. Try again later."}
    SessionLock.acquire()
    try:
        dataMessages = DbCollections.getDataMessages(sensorId).find()
        if dataMessages is None:
            return {"status": "OK", "StatusMessage": "No Data Found"}
        # Clean out the summary stats.
        sensorObj = SensorDb.getSensorObj(sensorId)
        sensorObj.cleanSensorStats()
        locationMessages = DbCollections.getLocationMessages().find(
            {SENSOR_ID: sensorId})
        for locationMessage in locationMessages:
            lid = locationMessage["_id"]
            LocationMessage.clean(locationMessage)
	    util.debugPrint("Location Message " + json.dumps(locationMessage, indent=4))
            DbCollections.getLocationMessages().update(
                {"_id": lid}, {"$set": locationMessage},
                upsert=False)
        cur = DbCollections.getDataMessages(sensorId).find(
            {SENSOR_ID: sensorId})

        # TODO -- recompute the occupancies. for data message.
        sensorObj.cleanSensorStats()
        for jsonData in cur:
            freqRange = DataMessage.getFreqRange(jsonData)
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
            DbCollections.getSensors().update({SENSOR_ID:sensorObj.getSensorId()},
                                               {"$set":sensorObj.getJson()},upsert=False)
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

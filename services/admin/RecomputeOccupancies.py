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
        if dataMessages is None:
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

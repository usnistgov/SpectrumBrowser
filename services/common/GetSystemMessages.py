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

import util
import DbCollections
import pymongo
import msgutils
from Defines import SENSOR_ID
from Defines import STATUS


def getSystemMessages(sensorId):
    util.debugPrint("getSystemMessages " + sensorId)
    query = {SENSOR_ID: sensorId}
    record = DbCollections.getSensors().find_one(query)
    if record is None:
        return {STATUS: "NOK", "StatusMessage": "Sensor not found"}
    cur = DbCollections.getSystemMessages().find({SENSOR_ID:sensorId})
    if cur is None or cur.count() == 0:
        return {STATUS: "OK", "StatusMessage": "System message not found"}
    else:
        systemMessages = []
        for systemMessage in cur:
            del systemMessage["_id"]
            if "_dataKey" in systemMessage:
                del systemMessage["_dataKey"]
            systemMessages.append(systemMessage)
        return {STATUS: "OK", "systemMessages": systemMessages}


def getLastSystemMessage(sensorId):
    """
    Get the last system message for a given sensor ID.
    """
    util.debugPrint("getSystemMessages " + sensorId)
    query = {SENSOR_ID: sensorId}
    record = DbCollections.getSensors().find_one(query)
    if record is None:
        return {STATUS: "NOK", "StatusMessage": "Sensor not found"}
    cur = DbCollections.getSystemMessages().find({SENSOR_ID:sensorId})
    if cur is None or cur.count() == 0:
        return {STATUS: "NOK", "StatusMessage": "System message not found"}
    else:
        cur.sort("t",pymongo.DESCENDING).limit(2)
        systemMessage = cur.next()
        del systemMessage["_id"]
        if "_dataKey" in systemMessage:
            del systemMessage["_dataKey"]
        return {STATUS: "OK", "systemMessage": systemMessage}


def getCalData(sensorId,timestamp):
    """
    Get the calibration data for a sensor ID given the system message timestamp.
    """
    util.debugPrint("getCalData " + sensorId + " timeStamp " + str(timestamp))
    query = {SENSOR_ID: sensorId, "t": timestamp}
    record = DbCollections.getSensors().find_one(query)
    if record is None:
        return {STATUS: "NOK", "StatusMessage": "Sensor not found"}

    systemMessage = DbCollections.getSystemMessages().find_one({SENSOR_ID:sensorId, "t": timestamp})

    if systemMessage is None:
        return {STATUS: "NOK", "StatusMessage": "System message not found"}

    calData = msgutils.getCalData(systemMessage)

    if calData is None:
        return {STATUS: "NOK", "StatusMessage": "Cal data not found"}
    else:
        return {STATUS: "OK", "calData": str(calData)}

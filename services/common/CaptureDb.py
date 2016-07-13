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


import DbCollections
from Defines import SENSOR_ID
from Defines import OK, NOK
from Defines import SECONDS_PER_DAY
from Defines import SENSOR_KEY
from Defines import STATUS
from Defines import TIME_ZONE_KEY
import timezone
import msgutils
import pymongo


def insertEvent(sensorId, captureEvent):
    """
    Insert an event in the capture database.
    """
    locationMessage = msgutils.getLocationMessage(captureEvent)
    if locationMessage is None:
        return {STATUS: NOK, "ErrorMessage": "Location message not found"}
    tZId = locationMessage[TIME_ZONE_KEY]
    del captureEvent[SENSOR_KEY]
    captureDb = DbCollections.getCaptureEventDb(sensorId)
    captureTime = captureEvent["t"]
    captureEvent["formattedTimeStamp"] = timezone.formatTimeStampLong(
        captureTime, tZId)
    captureDb.ensure_index([('t', pymongo.DESCENDING)])
    captureDb.insert(captureEvent)
    return {STATUS: OK}


def updateEvent(eventId, newEvent):
    """
    Update a capture event (add forensics information)
    """
    sensorId = newEvent[SENSOR_ID]
    captureDb = DbCollections.getCaptureEventDb(sensorId)
    result = captureDb.update({"_id": eventId}, {"$set": newEvent},
                              upsert=False)
    if result['n'] != 0:
        return {STATUS: OK}
    else:
        return {STATUS: NOK, "ErrorMessage": "Event not found"}


def deleteEvent(sensorId, eventTime):
    captureDb = DbCollections.getCaptureEventDb(sensorId)
    query = {SENSOR_ID: sensorId, "t": eventTime}
    captureDb.remove(query)
    return {STATUS: OK}


def getEvent(sensorId, eventTime):
    captureDb = DbCollections.getCaptureEventDb(sensorId)
    query = {SENSOR_ID: sensorId, "t": eventTime}
    return captureDb.find_one(query)


def getEvents(sensorId, startTime, days):
    captureDb = DbCollections.getCaptureEventDb(sensorId)
    if startTime > 0:
        query = {SENSOR_ID: sensorId, "t": {"$gte": startTime}}
        captureEvent = captureDb.find_one(query)
        if captureEvent is None:
            return {STATUS: OK, "events": []}
        locationMessage = msgutils.getLocationMessage(captureEvent)
        if locationMessage is None:
            return {STATUS: NOK, "ErrorMessage": "Location message not found"}
        tZId = locationMessage[TIME_ZONE_KEY]
        timeStamp = captureEvent['t']
        startTimeDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(
            timeStamp, tZId)
        endTime = startTimeDayBoundary + days * SECONDS_PER_DAY
        query = {"t": {"$gte": startTimeDayBoundary}, "t": {"$lte": endTime}}
    else:
        query = {}
        captureEvent = captureDb.find_one()
        if captureEvent is None:
            return {STATUS: OK, "events": []}
        locationMessage = msgutils.getLocationMessage(captureEvent)
        if locationMessage is None:
            return {STATUS: NOK, "ErrorMessage": "Location message not found"}
        timeStamp = captureEvent['t']
        tZId = locationMessage[TIME_ZONE_KEY]
        startTime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(timeStamp,
                                                                     tZId)
        if days > 0:
            endTime = startTime + days * SECONDS_PER_DAY
            query = {"t": {"$gte": startTime}, "t": {"$lte": endTime}}
        else:
            query = {"t": {"$gte": startTime}}

    found = captureDb.find(query)
    retval = []
    if found is not None:
        for value in found:
            del value["_id"]
            retval.append(value)

    return {STATUS: OK, "events": retval}


def deleteCaptureDb(sensorId, t=0):
    captureDb = DbCollections.getCaptureEventDb(sensorId)
    if t == 0:
        query = {SENSOR_ID: sensorId}
    else:
        query = {SENSOR_ID: sensorId, "t": {"$gte": t}}
    captureDb.remove(query)
    return {STATUS: OK}

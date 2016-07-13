#! /usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
# This software was developed by employees of the National Institute of
# Standards and Technology (NIST), and others.
# This software has been contributed to the public domain.
# Pursuant to title 15 Untied States Code Section 105, works of NIST
# employees are not subject to copyright protection in the United States
# and are considered to be in the public domain.
# As a result, a formal license is not needed to use this software.
#
# This software is provided "AS IS."
# NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
# OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
# AND DATA ACCURACY.  NIST does not warrant or make any representations
# regarding the use of the software or the results thereof, including but
# not limited to the correctness, accuracy, reliability or usefulness of
# this software.
'''
Created on Feb 3, 2015

@author: local
'''

from Defines import SENSOR_ID
from Defines import SENSOR_KEY
from Defines import SENSOR_ADMIN_EMAIL
from Defines import SENSOR_STATUS
from Defines import LOCAL_DB_INSERTION_TIME
from Defines import DATA_RETENTION_DURATION_MONTHS
from Defines import SENSOR_THRESHOLDS
from Defines import SENSOR_STREAMING_PARAMS
from Defines import STREAMING_SECONDS_PER_FRAME
from Defines import STREAMING_SAMPLING_INTERVAL_SECONDS
from Defines import STREAMING_FILTER
from Defines import IS_STREAMING_CAPTURE_ENABLED
from Defines import IS_STREAMING_ENABLED

from Defines import MEASUREMENT_TYPE

from Defines import SYS
from Defines import LOC
from Defines import DATA

import DbCollections
import msgutils
import timezone
import sys
import traceback
import pymongo
import Message


class Sensor(object):
    '''
    The sensor class that wraps a sensor object.
    '''

    def __init__(self, sensor):
        '''
        Constructor
        '''
        if "_id" in sensor:
            del sensor["_id"]
        self.sensor = sensor

    def getSensorId(self):
        return self.sensor[SENSOR_ID]

    def getSensorKey(self):
        return self.sensor[SENSOR_KEY]

    def getSensorAdminEmailAddress(self):
        return self.sensor(SENSOR_ADMIN_EMAIL)

    def getSensorDataRetentionDurationMonths(self):
        return self.sensor[DATA_RETENTION_DURATION_MONTHS]

    def getSensorStatus(self):
        return self.sensor[SENSOR_STATUS]

    def getLastMessageDate(self):
        lastSystemMessage = DbCollections.getSystemMessages().find_one(
            {SENSOR_ID: self.getSensorId()})
        lastMessageTime = 0

        if lastSystemMessage is None:
            return "NONE", "NONE"
        elif lastSystemMessage[LOCAL_DB_INSERTION_TIME] > lastMessageTime:
            lastMessageTime = lastSystemMessage[LOCAL_DB_INSERTION_TIME]
            lastMessageType = SYS
        lastLocationMessage = DbCollections.getLocationMessages().find_one(
            {SENSOR_ID: self.getSensorId()})
        if lastLocationMessage is not None and lastLocationMessage[
                LOCAL_DB_INSERTION_TIME] > lastMessageTime:
            lastMessageTime = lastLocationMessage[LOCAL_DB_INSERTION_TIME]
            lastMessageType = LOC
        lastDataMessage = msgutils.getLastSensorAcquisition(self.getSensorId())
        if lastDataMessage is not None and lastDataMessage[
                LOCAL_DB_INSERTION_TIME] > lastMessageTime:
            lastMessageTime = lastDataMessage[LOCAL_DB_INSERTION_TIME]
            lastMessageType = DATA
        return lastMessageType, timezone.getDateTimeFromLocalTimeStamp(
            lastMessageTime)

    def getActiveBand(self):
        thresholds = self.sensor[SENSOR_THRESHOLDS]
        for threshold in thresholds.values():
            if threshold["active"]:
                return threshold
        return None

    def isBandActive(self, sys2detect, minFreq, maxFreq):
        thresholds = self.sensor[SENSOR_THRESHOLDS]
        for threshold in thresholds.values():
            bandIsActive = (threshold["active"] and
                            threshold["minFreqHz"] == minFreq and
                            threshold["maxFreqHz"] == maxFreq and
                            threshold["systemToDetect"] == sys2detect)
            if bandIsActive:
                return True

        return False

    def getLastDataMessageDate(self):
        cur = DbCollections.getDataMessages(self.getSensorId()).find(
            {SENSOR_ID: self.getSensorId()}, {'_id': 0,
                                              'cutoff': 0,
                                              'locationMessageId': 0,
                                              'systemMessageId': 0,
                                              'seqNo': 0})
        if cur is None or cur.count() == 0:
            return "NONE"
        sortedCur = cur.sort("t", pymongo.DESCENDING)
        lastMessage = sortedCur.next()
        lastMessageTime = Message.getInsertionTime(lastMessage)
        lastMessageData = msgutils.getData(lastMessage)
        del lastMessage["_localDbInsertionTime"]
        return timezone.getDateTimeFromLocalTimeStamp(
            lastMessageTime), lastMessage, lastMessageData

    def getLastSystemMessageDate(self):
        cur = DbCollections.getSystemMessages().find(
            {SENSOR_ID: self.getSensorId()}, {'_id': 0})
        if cur is None or cur.count() == 0:
            return "NONE"
        sortedCur = cur.sort("t", pymongo.DESCENDING)
        lastSystemMessage = sortedCur.next()
        lastMessageTime = Message.getInsertionTime(lastSystemMessage)
        lastMessageData = msgutils.getCalData(lastSystemMessage)
        del lastSystemMessage["_localDbInsertionTime"]
        return timezone.getDateTimeFromLocalTimeStamp(
            lastMessageTime), lastSystemMessage, lastMessageData

    def getLastLocationMessageDate(self):
        queryId = {SENSOR_ID: self.getSensorId()}
        queryParams = {'_id': 0,
                       'sensorFreq': 0,
                       'firstDataMessageTimeStamp': 0,
                       'lastDataMessageTimeStamp': 0,
                       'maxOccupancy': 0,
                       'minOccupancy': 0,
                       'maxPower': 0,
                       'minPower': 0}
        cur = DbCollections.getLocationMessages().find(queryId, queryParams)
        if cur is None or cur.count() == 0:
            return "NONE"
        sortedCur = cur.sort("t", pymongo.DESCENDING)
        lastMessage = sortedCur.next()
        lastMessageTime = Message.getInsertionTime(lastMessage)
        del lastMessage["_localDbInsertionTime"]
        return timezone.getDateTimeFromLocalTimeStamp(
            lastMessageTime), lastMessage

    def getFirstDataMessageDate(self):
        cur = DbCollections.getDataMessages(self.getSensorId()).find(
            {SENSOR_ID: self.getSensorId()}, {'_id': 0,
                                              'cutoff': 0,
                                              'locationMessageId': 0,
                                              'systemMessageId': 0,
                                              'seqNo': 0})
        if cur is None or cur.count() == 0:
            return "NONE"
        sortedCur = cur.sort("t", pymongo.ASCENDING)
        lastMessage = sortedCur.next()
        lastMessageTime = Message.getInsertionTime(lastMessage)
        lastMessageData = msgutils.getData(lastMessage)
        del lastMessage["_localDbInsertionTime"]
        return timezone.getDateTimeFromLocalTimeStamp(
            lastMessageTime), lastMessage, lastMessageData

    def getFirstLocationMessageDate(self):
        queryId = {SENSOR_ID: self.getSensorId()}
        queryParams = {'_id': 0,
                       'sensorFreq': 0,
                       'firstDataMessageTimeStamp': 0,
                       'lastDataMessageTimeStamp': 0,
                       'maxOccupancy': 0,
                       'minOccupancy': 0,
                       'maxPower': 0,
                       'minPower': 0}
        cur = DbCollections.getLocationMessages().find(queryId, queryParams)
        if cur is None or cur.count() == 0:
            return "NONE"
        sortedCur = cur.sort("t", pymongo.ASCENDING)
        lastMessage = sortedCur.next()
        lastMessageTime = Message.getInsertionTime(lastMessage)
        del lastMessage["_localDbInsertionTime"]
        return (timezone.getDateTimeFromLocalTimeStamp(lastMessageTime),
                lastMessage)

    def getFirstSystemMessageDate(self):
        queryId = {SENSOR_ID: self.getSensorId()}
        queryParams = {'_id': 0}
        cur = DbCollections.getSystemMessages().find(queryId, queryParams)
        if cur is None or cur.count() == 0:
            return "NONE"
        sortedCur = cur.sort("t", pymongo.ASCENDING)
        lastMessage = sortedCur.next()
        lastMessageTime = Message.getInsertionTime(lastMessage)
        lastMessageData = msgutils.getCalData(lastMessage)
        del lastMessage["_localDbInsertionTime"]
        return timezone.getDateTimeFromLocalTimeStamp(
            lastMessageTime), lastMessage, lastMessageData

    def getStreamingParameters(self):
        return self.sensor[SENSOR_STREAMING_PARAMS]

    def getThreshold(self):
        return self.sensor[SENSOR_THRESHOLDS]

    def getMeasurementType(self):
        return self.sensor[MEASUREMENT_TYPE]

    def isStreamingEnabled(self):
        return self.sensor[IS_STREAMING_ENABLED]

    def isStreamingCaptureEnabled(self):
        r = (IS_STREAMING_CAPTURE_ENABLED in self.getStreamingParameters() and
             self.getStreamingParameters()[IS_STREAMING_CAPTURE_ENABLED])
        return r

    def getStreamingSecondsPerFrame(self):
        """
        Get the number of seconds per each frame sent to the browser.
        """
        params = self.getStreamingParameters()
        if params and STREAMING_SECONDS_PER_FRAME in params:
            return params[STREAMING_SECONDS_PER_FRAME]
        else:
            return -1

    def getStreamingSamplingIntervalSeconds(self):
        """
        Get the seconds for each capture.
        """
        params = self.getStreamingParameters()
        if params and STREAMING_SAMPLING_INTERVAL_SECONDS in params:
            return params[STREAMING_SAMPLING_INTERVAL_SECONDS]
        else:
            return -1

    def getStreamingFilter(self):
        """
        Get the streaming filter (MAX_HOLD or AVERAGE)
        """
        params = self.getStreamingParameters()
        if params and STREAMING_FILTER in params:
            return params[STREAMING_FILTER]
        else:
            return None

    def getSensor(self):
        """
        Get the sensor summary (sent back to the browser for display on admin
        interface).  This includes the first and last message dates and JSON.
        """
        try:
            firstLocMsgDate, firstLocMsg = self.getFirstLocationMessageDate()
            lastLocMsgDate, lastLocMsg = self.getLastLocationMessageDate()
            firstSysMsgDate, firstSysMsg = self.getFirstSystemMessageDate()
            lastSysMsgDate, lastSysMsg = self.getLastSystemMessageDate()
            firstDataMsgDate, firstDataMsg = self.getFirstDataMessageDate()
            lastDataMsgDate, lastDataMsg = self.getLastDataMessageDate()
        except IndexError:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            raise

        lastMessages = {"FIRST_LOCATION_MESSAGE_DATE": firstLocMsgDate,
                        "LAST_LOCATION_MESSAGE_DATE": lastLocMsgDate,
                        "FIRST_SYSTEM_MESSAGE_DATE": firstSysMsgDate,
                        "LAST_SYSTEM_MESSAGE_DATE": lastSysMsgDate,
                        "FIRST_DATA_MESSAGE_DATE": firstDataMsgDate,
                        "LAST_DATA_MESSAGE_DATE": lastDataMsgDate}

        lastJsons = {"FIRST_LOCATION_MESSAGE": firstLocMsg,
                     "LAST_LOCATION_MESSAGE": lastLocMsg,
                     "FIRST_SYSTEM_MESSAGE": firstSysMsg,
                     "LAST_SYSTEM_MESSAGE": lastSysMsg,
                     "FIRST_DATA_MESSAGE": firstDataMsg,
                     "LAST_DATA_MESSAGE": lastDataMsg}

        self.sensor["messageDates"] = lastMessages
        self.sensor["messageJsons"] = lastJsons
        return self.sensor

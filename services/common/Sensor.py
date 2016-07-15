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
from Defines import DATA_RETENTION_DURATION_MONTHS
from Defines import SENSOR_THRESHOLDS
from Defines import SENSOR_STREAMING_PARAMS
from Defines import STREAMING_SECONDS_PER_FRAME
from Defines import STREAMING_SAMPLING_INTERVAL_SECONDS
from Defines import STREAMING_FILTER
from Defines import IS_STREAMING_CAPTURE_ENABLED
from Defines import IS_STREAMING_ENABLED

from Defines import MEASUREMENT_TYPE

import DbCollections
import timezone
import sys
import traceback
import numpy as np

LAST_MESSAGE_DATE = "LAST_MESSAGE_DATE"
LAST_DATA_MESSAGE_DATE = "LAST_DATA_MESSAGE_DATE"
LAST_LOCATION_MESSAGE_DATE = "LAST_LOCATION_MESSAGE_DATE"
LAST_SYSTEM_MESSAGE_DATE = "LAST_SYSTEM_MESSAGE_DATE"
FIRST_DATA_MESSAGE_DATE = "FIRST_DATA_MESSAGE_DATE"
FIRST_LOCATION_MESSAGE_DATE = "FIRST_LOCATION_MESSAGE_DATE"
FIRST_SYSTEM_MESSAGE_DATE = "FIRST_SYSTEM_MESSAGE_DATE"


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
        if LAST_MESSAGE_DATE not in self.sensor:
            lastMessageTimeStamp = 0
        else:
            lastMessageTimeStamp = self.sensor[LAST_MESSAGE_DATE]
        return timezone.getDateTimeFromLocalTimeStamp(lastMessageTimeStamp)

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
        if LAST_DATA_MESSAGE_DATE not in self.sensor:
            lastMessageTimeStamp = 0
        else:
            lastMessageTimeStamp = self.sensor[LAST_DATA_MESSAGE_DATE]

        messages = DbCollections.getDataMessages(self.sensor[SENSOR_ID])
        lastMessage = messages.find_one({"t": lastMessageTimeStamp})
        if lastMessage:
            del lastMessage["_id"]
            t = lastMessage["_localDbInsertionTime"]
            return timezone.getDateTimeFromLocalTimeStamp(t), lastMessage
        else:
            return "NONE", {}

    def getLastSystemMessageDate(self):
        if LAST_SYSTEM_MESSAGE_DATE not in self.sensor:
            lastMessageTimeStamp = 0
        else:
            lastMessageTimeStamp = self.sensor[LAST_SYSTEM_MESSAGE_DATE]

        messages = DbCollections.getSystemMessages()
        query = {"t": lastMessageTimeStamp, SENSOR_ID: self.sensor[SENSOR_ID]}
        lastMessage = messages.find_one(query)
        if lastMessage:
            del lastMessage["_id"]
            t = lastMessage["_localDbInsertionTime"]
            return timezone.getDateTimeFromLocalTimeStamp(t), lastMessage
        else:
            return "NONE", {}

    def getLastLocationMessageDate(self):
        if LAST_LOCATION_MESSAGE_DATE not in self.sensor:
            lastMessageTimeStamp = 0
        else:
            lastMessageTimeStamp = self.sensor[LAST_LOCATION_MESSAGE_DATE]

        messages = DbCollections.getLocationMessages()
        query = {"t": lastMessageTimeStamp, SENSOR_ID: self.sensor[SENSOR_ID]}
        lastMessage = messages.find_one(query)

        if lastMessage:
            del lastMessage["_id"]
            t = lastMessage["_localDbInsertionTime"]
            return timezone.getDateTimeFromLocalTimeStamp(t), lastMessage
        else:
            return "NONE", {}

    def getFirstDataMessageDate(self):
        if FIRST_DATA_MESSAGE_DATE not in self.sensor:
            lastMessageTimeStamp = 0
        else:
            lastMessageTimeStamp = self.sensor[FIRST_DATA_MESSAGE_DATE]

        messages = DbCollections.getDataMessages(self.sensor[SENSOR_ID])
        lastMessage = messages.find_one({"t": lastMessageTimeStamp})

        if lastMessage:
            del lastMessage["_id"]
            t = lastMessage["_localDbInsertionTime"]
            return timezone.getDateTimeFromLocalTimeStamp(t), lastMessage
        else:
            return "NONE", {}

    def getFirstLocationMessageDate(self):
        lastMessage = None
        if FIRST_LOCATION_MESSAGE_DATE not in self.sensor:
            lastMessageTimeStamp = 0
        else:
            messages = DbCollections.getLocationMessages()
            lastMessageTimeStamp = self.sensor[FIRST_LOCATION_MESSAGE_DATE]
            query = {"t": lastMessageTimeStamp,
                     SENSOR_ID: self.sensor[SENSOR_ID]}
            lastMessage = messages.find_one(query)

        if lastMessage is not None:
            del lastMessage["_id"]
            t = lastMessage["_localDbInsertionTime"]
            return timezone.getDateTimeFromLocalTimeStamp(t), lastMessage
        else:
            return "NONE", {}

    def getFirstSystemMessageDate(self):
        if FIRST_SYSTEM_MESSAGE_DATE not in self.sensor:
            messageTimeStamp = 0
        else:
            messageTimeStamp = self.sensor[FIRST_SYSTEM_MESSAGE_DATE]

        messages = DbCollections.getSystemMessages()
        query = {"t": messageTimeStamp, SENSOR_ID: self.sensor[SENSOR_ID]}
        message = messages.find_one(query)
        if message:
            del message["_id"]
            t = message["_localDbInsertionTime"]
            return timezone.getDateTimeFromLocalTimeStamp(t), message
        else:
            return "NONE", {}

    def updateDataMessageTimeStamp(self, timeStamp):
        if FIRST_DATA_MESSAGE_DATE not in self.sensor:
            self.sensor[FIRST_DATA_MESSAGE_DATE] = timeStamp
            self.sensor[LAST_DATA_MESSAGE_DATE] = timeStamp
        else:
            self.sensor[LAST_DATA_MESSAGE_DATE] = timeStamp

    def updateLocationMessageTimeStamp(self, timeStamp):
        if FIRST_LOCATION_MESSAGE_DATE not in self.sensor:
            self.sensor[FIRST_LOCATION_MESSAGE_DATE] = timeStamp
            self.sensor[LAST_LOCATION_MESSAGE_DATE] = timeStamp
        else:
            self.sensor[LAST_LOCATION_MESSAGE_DATE] = timeStamp

    def updateSystemMessageTimeStamp(self, timeStamp):
        if FIRST_SYSTEM_MESSAGE_DATE not in self.sensor:
            self.sensor[FIRST_SYSTEM_MESSAGE_DATE] = timeStamp
            self.sensor[LAST_SYSTEM_MESSAGE_DATE] = timeStamp
        else:
            self.sensor[LAST_SYSTEM_MESSAGE_DATE] = timeStamp

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

    def updateMaxOccupancy(self, bandName, maxOccupancy):
        """
        Update the max occupancy.
        """
        if "maxOccupancy" not in self.sensor[SENSOR_THRESHOLDS][bandName]:
            self.sensor[SENSOR_THRESHOLDS][bandName][
                "maxOccupancy"] = maxOccupancy
        else:
            self.sensor[SENSOR_THRESHOLDS][bandName][
                "maxOccupancy"] = np.maximum(
                    maxOccupancy,
                    self.sensor[SENSOR_THRESHOLDS][bandName]["maxOccupancy"])

    def updateMinOccupancy(self, bandName, minOccupancy):
        if "minOccupancy" not in self.sensor[SENSOR_THRESHOLDS][bandName]:
            self.sensor[SENSOR_THRESHOLDS][bandName][
                "minOccupancy"] = minOccupancy
        else:
            self.sensor[SENSOR_THRESHOLDS][bandName][
                "minOccupancy"] = np.minimum(
                    minOccupancy,
                    self.sensor[SENSOR_THRESHOLDS][bandName]["minOccupancy"])

    def updateOccupancyCount(self, bandName, occupancy):
        if "occupancySum" not in self.sensor[SENSOR_THRESHOLDS][bandName]:
            self.sensor[SENSOR_THRESHOLDS][bandName][
                "occupancySum"] = occupancy
            self.sensor[SENSOR_THRESHOLDS][bandName]["acquisitionCount"] = 1
        else:
            self.sensor[SENSOR_THRESHOLDS][bandName][
                "acquisitionCount"] = self.sensor[SENSOR_THRESHOLDS][bandName][
                    "acquisitionCount"] + 1
            self.sensor[SENSOR_THRESHOLDS][bandName][
                "occupancySum"] = occupancy + self.sensor[SENSOR_THRESHOLDS][
                    bandName]["occupancySum"]

    def getMeanOccupancy(self, bandName):
        if "occupancySum" not in self.sensor[SENSOR_THRESHOLDS][bandName]:
            return 0
        else:
            occupancySum = self.sensor[SENSOR_THRESHOLDS][bandName][
                "occupancySum"]
            occupancyCount = self.sensor[SENSOR_THRESHOLDS][bandName][
                "aquisitionCount"]
            meanOccupancy = occupancySum / occupancyCount
            return meanOccupancy

    def updateTime(self, bandName, t):
        if "minTime" not in self.sensor[SENSOR_THRESHOLDS][bandName]:
            self.sensor[SENSOR_THRESHOLDS][bandName]["minTime"] = t
            self.sensor[SENSOR_THRESHOLDS][bandName]["maxTime"] = t
        else:
            self.sensor[SENSOR_THRESHOLDS][bandName]["minTime"] = np.minimum(
                t, self.sensor[SENSOR_THRESHOLDS][bandName]["minTime"])
            self.sensor[SENSOR_THRESHOLDS][bandName]["maxTime"] = np.maximum(
                t, self.sensor[SENSOR_THRESHOLDS][bandName]["maxTime"])

    def getMinMaxTime(self, bandName):
        if "minTime" not in self.sensor[SENSOR_THRESHOLDS][bandName]:
            return (0, 0)
        else:
            return (self.sensor[SENSOR_THRESHOLDS][bandName]["minTime"],
                    self.sensor[SENSOR_THRESHOLDS][bandName]["maxTime"])

    def cleanSensorStats(self):
        for bandName in self.sensor[SENSOR_THRESHOLDS].keys():
            band = self.sensor[SENSOR_THRESHOLDS][bandName]
            if "minOccupancy" in band:
                del self.sensor[SENSOR_THRESHOLDS][bandName]["minOccupancy"]
            if "maxOccupancy" in band:
                del self.sensor[SENSOR_THRESHOLDS][bandName]["maxOccupancy"]
            if "minTime" in band:
                del self.sensor[SENSOR_THRESHOLDS][bandName]["minTime"]
            if "occupancySum" in band:
                del self.sensor[SENSOR_THRESHOLDS][bandName]["occupancySum"]
            if "acquisitionCount" in band:
                del self.sensor[SENSOR_THRESHOLDS][bandName][
                    "acquisitionCount"]

        if FIRST_DATA_MESSAGE_DATE in self.sensor:
            del self.sensor[FIRST_DATA_MESSAGE_DATE]
        if LAST_DATA_MESSAGE_DATE in self.sensor:
            del self.sensor[LAST_DATA_MESSAGE_DATE]

        if FIRST_SYSTEM_MESSAGE_DATE in self.sensor:
            del self.sensor[FIRST_SYSTEM_MESSAGE_DATE]
        if LAST_SYSTEM_MESSAGE_DATE in self.sensor:
            del self.sensor[LAST_SYSTEM_MESSAGE_DATE]

        if FIRST_LOCATION_MESSAGE_DATE in self.sensor:
            del self.sensor[FIRST_LOCATION_MESSAGE_DATE]
        if LAST_LOCATION_MESSAGE_DATE in self.sensor:
            del self.sensor[LAST_LOCATION_MESSAGE_DATE]

    def getJson(self):
        return self.sensor

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

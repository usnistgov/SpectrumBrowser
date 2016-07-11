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
from Defines import STREAMING_CAPTURE_SAMPLE_SIZE_SECONDS
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
	if not LAST_MESSAGE_DATE in self.sensor:
	   lastMessageTimeStamp = 0
	else:
           lastMessageTimeStamp = self.sensor[LAST_MESSAGE_DATE] 
        return lastMessageType, timezone.getDateTimeFromLocalTimeStamp(lastMessageTime)

    def getActiveBand(self):
        thresholds = self.sensor[SENSOR_THRESHOLDS]
        for threshold in thresholds.values():
            if threshold["active"]:
                return threshold
        return None

    def isBandActive(self,sys2detect,minFreq,maxFreq):
        thresholds = self.sensor[SENSOR_THRESHOLDS]
        for threshold in thresholds.values():
            if threshold["active"] and threshold["minFreqHz"] == minFreq \
		and threshold["maxFreqHz"] == maxFreq and  \
                threshold["systemToDetect"] == sys2detect:
                return True
        return False

    def getLastDataMessageDate(self):
	if not LAST_DATA_MESSAGE_DATE in self.sensor:
	   lastMessageTimeStamp = 0
	else:
           lastMessageTimeStamp = self.sensor[LAST_DATA_MESSAGE_DATE] 
	lastMessage = DbCollections.getDataMessages(self.sensor[SENSOR_ID]).find_one({"t":lastMessageTimeStamp})
	if lastMessage == None:
	   return "NONE",{}
	else:
	   del lastMessage["_id"]
           return timezone.getDateTimeFromLocalTimeStamp(lastMessage["_localDbInsertionTime"]), lastMessage

    def getLastSystemMessageDate(self):
	if not LAST_SYSTEM_MESSAGE_DATE in self.sensor:
	   lastMessageTimeStamp = 0
	else:
           lastMessageTimeStamp = self.sensor[LAST_SYSTEM_MESSAGE_DATE] 
	lastMessage = DbCollections.getSystemMessages().find_one({"t":lastMessageTimeStamp,SENSOR_ID:self.sensor[SENSOR_ID]})
	if lastMessage == None:
	   return "NONE",{}
	else:
	   del lastMessage["_id"]
           return timezone.getDateTimeFromLocalTimeStamp(lastMessage["_localDbInsertionTime"]), lastMessage

    def getLastLocationMessageDate(self):
	if not LAST_LOCATION_MESSAGE_DATE in self.sensor:
	   lastMessageTimeStamp = 0
	else:
           lastMessageTimeStamp = self.sensor[LAST_LOCATION_MESSAGE_DATE] 
	lastMessage = DbCollections.getLocationMessages().find_one({"t":lastMessageTimeStamp,SENSOR_ID:self.sensor[SENSOR_ID]})
	if lastMessage == None:
	   return "NONE",{}
	else:
	   del lastMessage["_id"]
           return timezone.getDateTimeFromLocalTimeStamp(lastMessage["_localDbInsertionTime"]), lastMessage

    def getFirstDataMessageDate(self):
	if not FIRST_DATA_MESSAGE_DATE in self.sensor:
	   lastMessageTimeStamp = 0
	else:
           lastMessageTimeStamp = self.sensor[FIRST_DATA_MESSAGE_DATE] 
	lastMessage = DbCollections.getDataMessages(self.sensor[SENSOR_ID]).find_one({"t":lastMessageTimeStamp})
	if lastMessage == None:
	   return "NONE",{}
	else:
	   del lastMessage["_id"]
           return timezone.getDateTimeFromLocalTimeStamp(lastMessage["_localDbInsertionTime"]), lastMessage

    def getFirstLocationMessageDate(self):
	if not FIRST_LOCATION_MESSAGE_DATE in self.sensor:
	   lastMessageTimeStamp = 0
	else:
           lastMessageTimeStamp = self.sensor[FIRST_LOCATION_MESSAGE_DATE] 
	lastMessage = DbCollections.getLocationMessages().find_one({"t":lastMessageTimeStamp,SENSOR_ID:self.sensor[SENSOR_ID]})
	if lastMessage == None:
	   return "NONE",{}
	else:
	   del lastMessage["_id"]
           return timezone.getDateTimeFromLocalTimeStamp(lastMessage["_localDbInsertionTime"]), lastMessage

    def getFirstSystemMessageDate(self):
	if not FIRST_SYSTEM_MESSAGE_DATE in self.sensor:
	   messageTimeStamp = 0
	else:
           messageTimeStamp = self.sensor[FIRST_SYSTEM_MESSAGE_DATE] 
	message = DbCollections.getSystemMessages().find_one({"t":messageTimeStamp,SENSOR_ID:self.sensor[SENSOR_ID]})
	if message == None:
	   return "NONE",{}
	else:
	   del message["_id"]
           return timezone.getDateTimeFromLocalTimeStamp(message["_localDbInsertionTime"]), message

    def updateDataMessageTimeStamp(self,timeStamp):
	if not FIRST_DATA_MESSAGE_DATE in self.sensor:
	   self.sensor[FIRST_DATA_MESSAGE_DATE] = timeStamp
	   self.sensor[LAST_DATA_MESSAGE_DATE] = timeStamp
        else:
	   self.sensor[LAST_DATA_MESSAGE_DATE] = timeStamp

    def updateLocationMessageTimeStamp(self,timeStamp):
	if not FIRST_LOCATION_MESSAGE_DATE in self.sensor:
	   self.sensor[FIRST_LOCATION_MESSAGE_DATE] = timeStamp
	   self.sensor[LAST_LOCATION_MESSAGE_DATE] = timeStamp
        else:
	   self.sensor[LAST_LOCATION_MESSAGE_DATE] = timeStamp

    def updateSystemMessageTimeStamp(self,timeStamp):
	if not FIRST_SYSTEM_MESSAGE_DATE in self.sensor:
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
        return IS_STREAMING_CAPTURE_ENABLED in self.getStreamingParameters() and\
             self.getStreamingParameters()[IS_STREAMING_CAPTURE_ENABLED]

    def getStreamingSecondsPerFrame(self):
        """
        Get the number of seconds per each frame sent to the browser.
        """
        if self.getStreamingParameters(
        ) != None and STREAMING_SECONDS_PER_FRAME in self.getStreamingParameters(
        ):
            return self.getStreamingParameters()[STREAMING_SECONDS_PER_FRAME]
        else:
            return -1

    def getStreamingSamplingIntervalSeconds(self):
        """
        Get the seconds for each capture.
        """
        if self.getStreamingParameters() != None and STREAMING_SAMPLING_INTERVAL_SECONDS in self.getStreamingParameters():
            return self.getStreamingParameters()[
                STREAMING_SAMPLING_INTERVAL_SECONDS]
        else:
            return -1

    def getStreamingFilter(self):
        """
        Get the streaming filter (MAX_HOLD or AVERAGE)
        """
        if self.getStreamingParameters() != None and STREAMING_FILTER in self.getStreamingParameters():
            return self.getStreamingParameters()[STREAMING_FILTER]
        else:
            return None

    def updateMaxOccupancy(self,bandName,maxOccupancy):
	"""
        Update the max occupancy.
        """
        if not "maxOccupancy" in self.sensor[SENSOR_THRESHOLDS][bandName]:
           self.sensor[SENSOR_THRESHOLDS][bandName]["maxOccupancy"] = maxOccupancy
        else:
           self.sensor[SENSOR_THRESHOLDS][bandName]["maxOccupancy"] = np.maximum(maxOccupancy,self.sensor[SENSOR_THRESHOLDS][bandName]["maxOccupancy"])

    def updateMinOccupancy(self,bandName,minOccupancy):
        if not "minOccupancy" in self.sensor[SENSOR_THRESHOLDS][bandName]:
           self.sensor[SENSOR_THRESHOLDS][bandName]["minOccupancy"] = minOccupancy
        else:
           self.sensor[SENSOR_THRESHOLDS][bandName]["minOccupancy"] = np.minimum(minOccupancy,self.sensor[SENSOR_THRESHOLDS][bandName]["minOccupancy"])

    def updateOccupancyCount(self,bandName,occupancy):
        if not "occupancySum" in self.sensor[SENSOR_THRESHOLDS][bandName]:
           self.sensor[SENSOR_THRESHOLDS][bandName]["occupancySum"] = occupancy
           self.sensor[SENSOR_THRESHOLDS][bandName]["acquisitionCount"] = 1
        else:
           self.sensor[SENSOR_THRESHOLDS][bandName]["acquisitionCount"] = self.sensor[SENSOR_THRESHOLDS][bandName]["acquisitionCount"] + 1
           self.sensor[SENSOR_THRESHOLDS][bandName]["occupancySum"] = occupancy + self.sensor[SENSOR_THRESHOLDS][bandName]["occupancySum"]

    def getMeanOccupancy(self,bandName):
        if not "occupancySum" in self.sensor[SENSOR_THRESHOLDS][bandName]:
	    return 0
	else:
            occupancySum = self.sensor[SENSOR_THRESHOLDS][bandName]["occupancySum"]
	    occupancyCount = self.sensor[SENSOR_THRESHOLDS][bandName]["aquisitionCount"]
	    meanOccupancy = occupancySum/occupancyCount
	    return meanOccupancy

    def updateTime(self,bandName,t):
	if not "minTime" in self.sensor[SENSOR_THRESHOLDS][bandName]:
	   self.sensor[SENSOR_THRESHOLDS][bandName]["minTime"] = t
	   self.sensor[SENSOR_THRESHOLDS][bandName]["maxTime"] = t
	else:
	   self.sensor[SENSOR_THRESHOLDS][bandName]["minTime"] = np.minimum(t,self.sensor[SENSOR_THRESHOLDS][bandName]["minTime"])
	   self.sensor[SENSOR_THRESHOLDS][bandName]["maxTime"] = np.maximum(t,self.sensor[SENSOR_THRESHOLDS][bandName]["maxTime"])
	   

    def getMinMaxTime(self,bandName):
	if not "minTime" in self.sensor[SENSOR_THRESHOLDS][bandName]:
	   return (0,0)
	else:
	   return (self.sensor[SENSOR_THRESHOLDS][bandName]["minTime"],self.sensor[SENSOR_THRESHOLDS][bandName]["maxTime"])

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
	    	del self.sensor[SENSOR_THRESHOLDS][bandName]["acquisitionCount"]

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
        Get the sensor summary (sent back to the browser for display on admin interface).
	This includes the first and last message dates and JSON.
        """
        try:
            lastMessages = {
                            FIRST_LOCATION_MESSAGE_DATE: self.getFirstLocationMessageDate()[0], \
                            LAST_LOCATION_MESSAGE_DATE:self.getLastLocationMessageDate()[0], \
                            FIRST_SYSTEM_MESSAGE_DATE:self.getFirstSystemMessageDate()[0], \
                            LAST_SYSTEM_MESSAGE_DATE:self.getLastSystemMessageDate()[0], \
                            FIRST_DATA_MESSAGE_DATE:self.getFirstDataMessageDate()[0], \
                            LAST_DATA_MESSAGE_DATE:self.getLastDataMessageDate()[0]
                           }

            lastJsons = {
                          "FIRST_LOCATION_MESSAGE":self.getFirstLocationMessageDate()[1], \
                          "LAST_LOCATION_MESSAGE":self.getLastLocationMessageDate()[1], \
                          "FIRST_SYSTEM_MESSAGE":self.getFirstSystemMessageDate()[1], \
                          "LAST_SYSTEM_MESSAGE":self.getLastSystemMessageDate()[1], \
                          "FIRST_DATA_MESSAGE":self.getFirstDataMessageDate()[1], \
                          "LAST_DATA_MESSAGE":self.getLastDataMessageDate()[1]
                       }

            self.sensor["messageDates"] = lastMessages
            self.sensor["messageJsons"] = lastJsons
            return self.sensor
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            raise

	

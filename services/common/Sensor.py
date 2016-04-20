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
        lastSystemMessage = DbCollections.getSystemMessages().find_one({SENSOR_ID:self.getSensorId()})
        lastMessageTime = 0

        if lastSystemMessage == None:
            return "NONE", "NONE"
        elif lastSystemMessage[LOCAL_DB_INSERTION_TIME] > lastMessageTime:
            lastMessageTime = lastSystemMessage[LOCAL_DB_INSERTION_TIME]
            lastMessageType = SYS
        lastLocationMessage = DbCollections.getLocationMessages().find_one({SENSOR_ID:self.getSensorId()})
        if lastLocationMessage != None and lastLocationMessage[LOCAL_DB_INSERTION_TIME] > lastMessageTime:
            lastMessageTime = lastLocationMessage[LOCAL_DB_INSERTION_TIME]
            lastMessageType = LOC
        lastDataMessage = msgutils.getLastSensorAcquisition(self.getSensorId())
        if lastDataMessage != None and lastDataMessage[LOCAL_DB_INSERTION_TIME] > lastMessageTime:
            lastMessageTime = lastDataMessage[LOCAL_DB_INSERTION_TIME]
            lastMessageType = DATA
        return lastMessageType, timezone.getDateTimeFromLocalTimeStamp(lastMessageTime)

    def getActiveBand(self):
	thresholds = self.sensor[SENSOR_THRESHOLDS]
	for threshold in thresholds.values():
	    if threshold["active"] :
		return threshold
	return None

    def getLastDataMessageDate(self):
        cur = DbCollections.getDataMessages(self.getSensorId()).find({SENSOR_ID:self.getSensorId()}, {'_id':0, 'cutoff':0, 'locationMessageId':0, 'systemMessageId':0, 'seqNo':0})
        if cur == None or cur.count() == 0:
            return "NONE"
        sortedCur = cur.sort("t", pymongo.DESCENDING)
        lastMessage = sortedCur.next()
        lastMessageTime = Message.getInsertionTime(lastMessage)
	lastMessageData = msgutils.getData(lastMessage)
	del lastMessage["_localDbInsertionTime"]
        return timezone.getDateTimeFromLocalTimeStamp(lastMessageTime), lastMessage, lastMessageData

    def getLastSystemMessageDate(self):
        cur = DbCollections.getSystemMessages().find({SENSOR_ID:self.getSensorId()}, {'_id':0})
        if cur == None or cur.count() == 0:
            return "NONE"
        sortedCur = cur.sort("t", pymongo.DESCENDING)
        lastSystemMessage = sortedCur.next()
        lastMessageTime = Message.getInsertionTime(lastSystemMessage)
	lastMessageData = msgutils.getCalData(lastSystemMessage)
	del lastSystemMessage["_localDbInsertionTime"]
        return timezone.getDateTimeFromLocalTimeStamp(lastMessageTime), lastSystemMessage, lastMessageData

    def getLastLocationMessageDate(self):
        cur = DbCollections.getLocationMessages().find({SENSOR_ID:self.getSensorId()}, {'_id':0, 'sensorFreq':0,  'firstDataMessageTimeStamp':0, 'lastDataMessageTimeStamp':0, 'maxOccupancy':0, 'minOccupancy':0, 'maxPower':0, 'minPower':0})
        if cur == None or cur.count() == 0:
            return "NONE"
        sortedCur = cur.sort("t", pymongo.DESCENDING)
        lastMessage = sortedCur.next()
        lastMessageTime = Message.getInsertionTime(lastMessage)
	del lastMessage["_localDbInsertionTime"]
        return timezone.getDateTimeFromLocalTimeStamp(lastMessageTime), lastMessage

    def getFirstDataMessageDate(self):
        cur = DbCollections.getDataMessages(self.getSensorId()).find({SENSOR_ID:self.getSensorId()}, {'_id':0, 'cutoff':0, 'locationMessageId':0, 'systemMessageId':0, 'seqNo':0})
        if cur == None or cur.count() == 0:
            return "NONE"
        sortedCur = cur.sort("t", pymongo.ASCENDING)
        lastMessage = sortedCur.next()
        lastMessageTime = Message.getInsertionTime(lastMessage)
	lastMessageData = msgutils.getData(lastMessage)
	del lastMessage["_localDbInsertionTime"]
        return timezone.getDateTimeFromLocalTimeStamp(lastMessageTime), lastMessage, lastMessageData

    def getFirstLocationMessageDate(self):
        cur = DbCollections.getLocationMessages().find({SENSOR_ID:self.getSensorId()}, {'_id':0, 'sensorFreq':0,  'firstDataMessageTimeStamp':0, 'lastDataMessageTimeStamp':0, 'maxOccupancy':0, 'minOccupancy':0, 'maxPower':0, 'minPower':0})
        if cur == None or cur.count() == 0:
            return "NONE"
        sortedCur = cur.sort("t", pymongo.ASCENDING)
        lastMessage = sortedCur.next()
        lastMessageTime = Message.getInsertionTime(lastMessage)
	del lastMessage["_localDbInsertionTime"]
        return timezone.getDateTimeFromLocalTimeStamp(lastMessageTime), lastMessage

    def getFirstSystemMessageDate(self):
        cur = DbCollections.getSystemMessages().find({SENSOR_ID:self.getSensorId()}, {'_id':0})
        if cur == None or cur.count() == 0:
            return "NONE"
        sortedCur = cur.sort("t", pymongo.ASCENDING)
        lastMessage = sortedCur.next()
        lastMessageTime = Message.getInsertionTime(lastMessage)
	lastMessageData = msgutils.getCalData(lastMessage)
	del lastMessage["_localDbInsertionTime"]
        return timezone.getDateTimeFromLocalTimeStamp(lastMessageTime), lastMessage, lastMessageData

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
	if self.getStreamingParameters() != None and STREAMING_SECONDS_PER_FRAME in self.getStreamingParameters():
       	   return self.getStreamingParameters()[STREAMING_SECONDS_PER_FRAME]
	else:
	   return -1

    def getStreamingSamplingIntervalSeconds(self):
        """
        Get the seconds for each capture.
        """
	if self.getStreamingParameters() != None and STREAMING_SAMPLING_INTERVAL_SECONDS in self.getStreamingParameters():
           return self.getStreamingParameters()[STREAMING_SAMPLING_INTERVAL_SECONDS]
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

    def getSensor(self):
        """
        Get the sensor summary (sent back to the browser for display on admin interface).
        """
        try :
            lastMessages = {
                            "FIRST_LOCATION_MESSAGE_DATE": self.getFirstLocationMessageDate()[0], \
                            "LAST_LOCATION_MESSAGE_DATE":self.getLastLocationMessageDate()[0], \
                            "FIRST_SYSTEM_MESSAGE_DATE":self.getFirstSystemMessageDate()[0], \
                            "LAST_SYSTEM_MESSAGE_DATE":self.getLastSystemMessageDate()[0], \
                            "FIRST_DATA_MESSAGE_DATE":self.getFirstDataMessageDate()[0], \
                            "LAST_DATA_MESSAGE_DATE":self.getLastDataMessageDate()[0]
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






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
    classdocs
    '''


    def __init__(self, sensor):
        '''
        Constructor
        '''
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
            return "NONE","NONE"
        elif lastSystemMessage[LOCAL_DB_INSERTION_TIME] > lastMessageTime:
            lastMessageTime = lastSystemMessage[LOCAL_DB_INSERTION_TIME]
            lastMessageType = SYS
        lastLocationMessage = DbCollections.getLocationMessages().find_one({SENSOR_ID:self.getSensorId()})
        if lastLocationMessage != None and lastLocationMessage[LOCAL_DB_INSERTION_TIME] > lastMessageTime:
            lastMessageTime = lastLocationMessage[LOCAL_DB_INSERTION_TIME]
            lastMessageType = LOC
        lastDataMessage = msgutils.getLastSensorAcquisition(self.getSensorId())
        if lastDataMessage  != None and lastDataMessage[LOCAL_DB_INSERTION_TIME] > lastMessageTime:
            lastMessageTime = lastDataMessage[LOCAL_DB_INSERTION_TIME]
            lastMessageType = DATA
        return lastMessageType,timezone.getDateTimeFromLocalTimeStamp(lastMessageTime)
    
    def getLastDataMessageDate(self):
        cur = DbCollections.getDataMessages(self.getSensorId()).find({SENSOR_ID:self.getSensorId()})
        if cur == None or cur.count() == 0:
            return "NONE"
        sortedCur = cur.sort("t",pymongo.DESCENDING)
        lastMessage = sortedCur.next()
        lastMessageTime = Message.getInsertionTime(lastMessage)
        return timezone.getDateTimeFromLocalTimeStamp(lastMessageTime)
        
    
    def getLastSystemMessageDate(self):
        cur = DbCollections.getSystemMessages().find({SENSOR_ID:self.getSensorId()})
        if cur == None or cur.count() == 0:
            return "NONE"
        sortedCur = cur.sort("t",pymongo.DESCENDING)
        lastSystemMessage = sortedCur.next()
        lastMessageTime = Message.getInsertionTime(lastSystemMessage)
        return timezone.getDateTimeFromLocalTimeStamp(lastMessageTime)
    
    def getLastLocationMessageDate(self):
        cur = DbCollections.getLocationMessages().find({SENSOR_ID:self.getSensorId()})
        if cur == None or cur.count() == 0:
            return "NONE"
        sortedCur = cur.sort("t",pymongo.DESCENDING)
        lastMessage = sortedCur.next()
        lastMessageTime = Message.getInsertionTime(lastMessage)
        return timezone.getDateTimeFromLocalTimeStamp(lastMessageTime)
    
    def getFirstDataMessageDate(self):
        cur = DbCollections.getDataMessages(self.getSensorId()).find({SENSOR_ID:self.getSensorId()})
        if cur == None or cur.count() == 0:
            return "NONE"
        sortedCur = cur.sort("t",pymongo.ASCENDING)
        lastMessage = sortedCur.next()
        lastMessageTime = Message.getInsertionTime(lastMessage)
        return timezone.getDateTimeFromLocalTimeStamp(lastMessageTime)
    
    def getFirstLocationMessageDate(self):
        cur = DbCollections.getLocationMessages().find({SENSOR_ID:self.getSensorId()})
        if cur == None or cur.count() == 0:
            return "NONE"
        sortedCur = cur.sort("t",pymongo.ASCENDING)
        lastMessage = sortedCur.next()
        lastMessageTime = Message.getInsertionTime(lastMessage)
        return timezone.getDateTimeFromLocalTimeStamp(lastMessageTime)
    
    def getFirstSystemMessageDate(self):
        cur = DbCollections.getSystemMessages().find({SENSOR_ID:self.getSensorId()})
        if cur == None or cur.count() == 0:
            return "NONE"
        sortedCur = cur.sort("t",pymongo.ASCENDING)
        lastMessage = sortedCur.next()
        lastMessageTime = Message.getInsertionTime(lastMessage)
        return timezone.getDateTimeFromLocalTimeStamp(lastMessageTime)

    def getStreamingParameters(self):
        return self.sensor[SENSOR_STREAMING_PARAMS]
    
    def getThreshold(self):
        return self.sensor[SENSOR_THRESHOLDS]
    
    def getMeasurementType(self):
        return self.sensor[MEASUREMENT_TYPE]
    
    def isStreamingEnabled(self):
        if  self.sensor[IS_STREAMING_ENABLED]:
            return True
        else:
            import json
            print (json.dumps(self.sensor))
            return False
        
    def isStreamingCaptureEnabled(self):
        return IS_STREAMING_CAPTURE_ENABLED in self.getStreamingParameters() and\
             self.getStreamingParameters()[IS_STREAMING_CAPTURE_ENABLED]
            
    
    def getStreamingSecondsPerFrame(self):
        return self.getStreamingParameters()[STREAMING_SECONDS_PER_FRAME]
    
    def getStreamingSamplingIntervalSeconds(self):
        return self.getStreamingParameters()[STREAMING_SAMPLING_INTERVAL_SECONDS]
    
    
    def getStreamingFilter(self):
        return self.getStreamingParameters()[STREAMING_FILTER]
    
    
    
    def getSensor(self):
        try :
            lastMessages = {"FIRST_LOCATION_MESSAGE": self.getFirstLocationMessageDate(),\
                            "LAST_LOCATION_MESSAGE":self.getLastLocationMessageDate(),\
                            "FIRST_SYSTEM_MESSAGE_DATE":self.getFirstSystemMessageDate(),\
                            "LAST_SYSTEM_MESSAGE_DATE":self.getLastSystemMessageDate(),\
                            "FIRST_DATA_MESSAGE_DATE":self.getFirstDataMessageDate(),\
                            "LAST_DATA_MESSAGE_DATE":self.getLastDataMessageDate()
                            }
            self.sensor["messageDates"] = lastMessages
            return self.sensor
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            raise
        
        
        
    
    
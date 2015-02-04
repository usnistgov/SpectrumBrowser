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
from Defines import LAST_MESSAGE_TYPE
from Defines import LAST_MESSAGE_DATE

from Defines import SYS
from Defines import LOC
from Defines import DATA

import DbCollections
import msgutils
import timezone
import sys
import traceback

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
        lastDataMessageTime = msgutils.getLastSensorAcquisition(self.getSensorId())
        if lastDataMessageTime > lastMessageTime:
            lastMessageTime = lastDataMessageTime
            lastMessageType = DATA
        return lastMessageType,timezone.getDateTimeFromLocalTimeStamp(lastMessageTime)
    

    
    def getStreamingParameters(self):
        return self.sensor[SENSOR_STREAMING_PARAMS]
    
    def getThreshold(self):
        return self.sensor[SENSOR_THRESHOLDS]
    
    def getSensor(self):
        try :
            self.sensor[LAST_MESSAGE_TYPE],self.sensor[LAST_MESSAGE_DATE] = self.getLastMessageDate()
            return self.sensor
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            raise
        
        
        
    
    
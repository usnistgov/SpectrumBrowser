'''
Created on Feb 2, 2015

@author: local
'''

SENSOR_ID = "SensorID"
SENSOR_KEY="SensorKey"
SENSOR_ADMIN_EMAIL = "sensorAdminEmail"
SENSOR_STATUS = "sensorStatus"
LOCAL_DB_INSERTION_TIME = "_localDbInsertionTime"
DATA_RETENTION_DURATION_MONTHS = "dataRetentionDurationMonths"
SENSOR_THRESHOLDS = "thresholds"
SENSOR_STREAMING_PARAMS = "streaming"
LAST_MESSAGE_TYPE = "lastMessageType"
LAST_MESSAGE_DATE = "lastMessageDate"
SENSOR_KEY = "SensorKey"


#Message Types

SYS = "Sys"
LOC = "Loc"
DATA = "Data"

# Streaming filter types
MAX_HOLD = "MAX_HOLD"

TIME_ZONE_KEY = "TimeZone"
SIXTY_DAYS = 60*60*60*60
HOURS_PER_DAY = 24
MINUTES_PER_DAY = HOURS_PER_DAY * 60
SECONDS_PER_DAY = MINUTES_PER_DAY * 60
MILISECONDS_PER_DAY = SECONDS_PER_DAY * 1000
UNDER_CUTOFF_COLOR = '#D6D6DB'
OVER_CUTOFF_COLOR = '#000000'

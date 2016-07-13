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
Created on Feb 2, 2015

@author: local
'''

SENSOR_ID = "SensorID"
SENSOR_KEY = "SensorKey"
SENSOR_ADMIN_EMAIL = "sensorAdminEmail"
SENSOR_STATUS = "sensorStatus"
LOCAL_DB_INSERTION_TIME = "_localDbInsertionTime"
DATA_RETENTION_DURATION_MONTHS = "dataRetentionDurationMonths"
SENSOR_THRESHOLDS = "thresholds"
SENSOR_STREAMING_PARAMS = "streaming"
STREAMING_SAMPLING_INTERVAL_SECONDS = "streamingSamplingIntervalSeconds"
STREAMING_SECONDS_PER_FRAME = "streamingSecondsPerFrame"
STREAMING_CAPTURE_SAMPLE_SIZE_SECONDS = "streamingCaptureSampleSizeSeconds"
STREAMING_FILTER = "streamingFilter"
IS_STREAMING_CAPTURE_ENABLED = "enableStreamingCapture"
LAST_MESSAGE_TYPE = "lastMessageType"
LAST_MESSAGE_DATE = "lastMessageDate"
CHANNEL_COUNT = "channelCount"
ACQUISITION_COUNT = "acquisitionCount"
MEASUREMENT_TYPE = "measurementType"
ENABLED = "ENABLED"
DISABLED = "DISABLED"
ACTIVE = "active"
PORT = "port"
NOISE_FLOOR = 'wnI'

LAT = "Lat"
LON = "Lon"
ALT = "Alt"
FFT_POWER = "FFT-Power"
SWEPT_FREQUENCY = "Swept-frequency"
FREQ_RANGE = "freqRange"
IS_STREAMING_ENABLED = "isStreamingEnabled"
STATIC_GENERATED_FILE_LOCATION = "static/spectrumbrowser/generated/"
URL = "url"
OCCUPANCY_START_TIME = "_occupancyStartTime"
OCCUPANCY_FILE_URL = "occupancy"
TIME_FILE_URL = "time"
POWER_FILE_URL = "power"

# configuration

UNKNOWN = "UNKNOWN"
API_KEY = "API_KEY"
HOST_NAME = "HOST_NAME"
PUBLIC_PORT = "PUBLIC_PORT"
PROTOCOL = "PROTOCOL"
IS_AUTHENTICATION_REQUIRED = "IS_AUTHENTICATION_REQUIRED"
MY_SERVER_ID = "MY_SERVER_ID"
MY_SERVER_KEY = "MY_SERVER_KEY"
SMTP_PORT = "SMTP_PORT"
SMTP_SERVER = "SMTP_SERVER"
SMTP_EMAIL_ADDRESS = "SMTP_EMAIL_ADDRESS"
ADMIN_CONTACT_NAME = "ADMIN_CONTACT_NAME"
ADMIN_CONTACT_NUMBER = "ADMIN_CONTACT_NUMBER"
SOFT_STATE_REFRESH_INTERVAL = "SOFT_STATE_REFRESH_INTERVAL"
USE_LDAP = "USE_LDAP"
ACCOUNT_NUM_FAILED_LOGIN_ATTEMPTS = "ACCOUNT_NUM_FAILED_LOGIN_ATTEMPTS"
CHANGE_PASSWORD_INTERVAL_DAYS = "CHANGE_PASSWORD_INTERVAL_DAYS"
ACCOUNT_REQUEST_TIMEOUT_HOURS = "ACCOUNT_REQUEST_TIMEOUT_HOURS"
ACCOUNT_USER_ACKNOW_HOURS = "ACCOUNT_USER_ACKNOW_HOURS"
USER_SESSION_TIMEOUT_MINUTES = "USER_SESSION_TIMEOUT_MINUTES"
ADMIN_SESSION_TIMEOUT_MINUTES = "ADMIN_SESSION_TIMEOUT_MINUTES"
CERT = "CERT"
PRIV_KEY = "PRIV_KEY"
MIN_STREAMING_INTER_ARRIVAL_TIME_SECONDS = "MIN_STREAMING_INTER_ARRIVAL_TIME_SECONDS"
ADMIN = "admin"
USER = "user"
SPECTRUMS_PER_FRAME = "_spectrumsPerFrame"
TIME_PER_MEASUREMENT = "timePerMeasurement"
STREAMING_FILTER = "streamingFilter"

# accounts
ACCOUNT_EMAIL_ADDRESS = "emailAddress"
ACCOUNT_FIRST_NAME = "firstName"
ACCOUNT_LAST_NAME = "lastName"
ACCOUNT_PASSWORD = "password"
ACCOUNT_PRIVILEGE = "privilege"
ACCOUNT_CREATION_TIME = "timeAccountCreated"
ACCOUNT_PASSWORD_EXPIRE_TIME = "timePasswordExpires"
ACCOUNT_NUM_FAILED_LOGINS = "numFailedLoginAttempts"
ACCOUNT_LOCKED = "accountLocked"
TEMP_ACCOUNT_TOKEN = "token"

# accounts, change password:
ACCOUNT_OLD_PASSWORD = "oldPassword"
ACCOUNT_NEW_PASSWORD = "newPassword"

# Message Types

SYS = "Sys"
LOC = "Loc"
DATA = "Data"
CAL = "Cal"
DATA_TYPE = "DataType"
DATA_KEY = "_dataKey"
OCCUPANCY_KEY = "_occupancyKey"
OCCUPANCY_VECTOR_LENGTH = "_occupancyVectorLength"

TYPE = "Type"
NOISE_FLOOR = "wnI"
SYS_TO_DETECT = "Sys2Detect"
THRESHOLD_DBM_PER_HZ = "thresholdDbmPerHz"
THRESHOLD_MIN_FREQ_HZ = "minFreqHz"
THRESHOLD_MAX_FREQ_HZ = "maxFreqHz"
THRESHOLD_SYS_TO_DETECT = "systemToDetect"
BINARY_INT8 = "Binary - int8"
BINARY_INT16 = "Binary - int16"
BINARY_FLOAT32 = "Binary - float32"
ASCII = "ASCII"

SERVICE_NAMES = ["servicecontrol", "admin", "spectrumbrowser", "streaming",
                 "occupancy", "monitoring", "federation", "spectrumdb"]
SERVICE_NAME = "serviceName"

# Streaming filter types
MAX_HOLD = "MAX_HOLD"

TIME_ZONE_KEY = "TimeZone"

ONE_HOUR = 60 * 60
TWO_HOURS = 2 * ONE_HOUR
FIFTEEN_MINUTES = 15 * 60
SECONDS_PER_HOUR = 60 * 60
HOURS_PER_DAY = 24
MILISECONDS_PER_SECOND = 1000
MINUTES_PER_DAY = HOURS_PER_DAY * 60
SECONDS_PER_DAY = MINUTES_PER_DAY * 60
MILISECONDS_PER_DAY = SECONDS_PER_DAY * MILISECONDS_PER_SECOND
STREAMING_SERVER_PORT = 9000
OCCUPANCY_ALERT_PORT = 9001
UNDER_CUTOFF_COLOR = '#D6D6DB'
OVER_CUTOFF_COLOR = '#000000'
MAP_WIDTH = "mapWidth"
MAP_HEIGHT = "mapHeight"
SPEC_WIDTH = "specWidth"
SPEC_HEIGHT = "specHeight"
CHART_WIDTH = "chartWidth"
CHART_HEIGHT = "chartHeight"

EXPIRE_TIME = "expireTime"
ERROR_MESSAGE = "ErrorMessage"
SERVICE_STATUS = "serviceStatus"
USER_ACCOUNTS = "userAccounts"
STATUS = "status"
STATUS_MESSAGE = "statusMessage"

USER_NAME = "userName"
SESSIONS = "sessions"
SESSION_ID = "sessionId"
SESSION_LOGIN_TIME = "timeLogin"
REMOTE_ADDRESS = "remoteAddress"
TIME = "t"
STATE = "state"
PENDING_FREEZE = "PENDING_FREEZE"
FROZEN = "FROZEN"
FREEZE_REQUESTER = "FREEZE_REQUESTER"

USER_SESSIONS = "userSessions"
ADMIN_SESSIONS = "adminSessions"

THRESHOLDS = "thresholds"
SYSTEM_TO_DETECT = "systemToDetect"
MIN_FREQ_HZ = "minFreqHz"
MAX_FREQ_HZ = "maxFreqHz"
BAND_STATISTICS = "bandStatistics"
MONGO_DIR = "MONGO_DIR"

COUNT = "count"
NOK = "NOK"
OK = "OK"
CUTOFF = "cutoff"
WARNING_TEXT = "WARNING_TEXT"
PASSWORD_EXPIRED_ERROR = "PASSWORD_EXPIRED_ERROR"
USERNAME_OR_PASSWORD_NOT_FOUND_ERROR = "Invalid email, password, or account privilege. Please try again."
ACCOUNT_LOCKED_ERROR = "ACCOUNT_LOCKED"

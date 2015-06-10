'''
Created on Apr 10, 2015

@author: local
'''
import DbCollections
import util
import msgutils
import DataMessage
import sys
import os
import traceback
import Config
from json import dumps
import timezone

from Defines import SENSOR_ID
from Defines import STATUS
from Defines import FREQ_RANGE
from Defines import TIME
from Defines import OCCUPANCY_VECTOR_LENGTH
from Defines import OCCUPANCY_KEY

from Defines import STATIC_GENERATED_FILE_LOCATION
from Defines import TIME_PER_MEASUREMENT

from Defines import SPECTRUMS_PER_FRAME
from Defines import STATUS_MESSAGE
from Defines import STREAMING_FILTER
from Defines import OCCUPANCY_START_TIME
from Defines import OCCUPANCY_FILE_URL
from Defines import TIME_FILE_URL

from Defines import CHANNEL_COUNT
from Defines import TIME_ZONE_KEY

from Defines import URL


def getOccupancies(sensorId,sys2detect,minFreq,maxFreq,startTime,seconds,sessionId):
    freqRange = msgutils.freqRange(sys2detect,minFreq,maxFreq)
    dataMessages = DbCollections.getDataMessages(sensorId)
    dataMessage = dataMessages.find_one({})
    if dataMessages == None:
        return {STATUS:"NOK", STATUS_MESSAGE: "No Data Found"}
    endTime = startTime + seconds
    query = {SENSOR_ID:sensorId,FREQ_RANGE:freqRange, "$and":[ {TIME:{"$gte":startTime}}, {TIME:{"$lte":endTime}}]}
    print query
    cur = dataMessages.find(query)
    if cur == None or cur.count() == 0:
        return {STATUS:"NOK", STATUS_MESSAGE: "No Data Found"}
    occupancyFileName = sessionId + "/" + sensorId + ":" + freqRange + ".occupancy." + str(startTime)+ "-" + str(seconds) + ".txt"
    if not os.path.exists(util.getPath(STATIC_GENERATED_FILE_LOCATION)  + sessionId):
         os.mkdir(util.getPath(STATIC_GENERATED_FILE_LOCATION)  + sessionId)
    occupancyFileUrl = Config.getGeneratedDataPath() + "/" + occupancyFileName
    occupancyFilePath = util.getPath(STATIC_GENERATED_FILE_LOCATION)  +  occupancyFileName
    occupancyFile = open(occupancyFilePath,"w")
    
    
    timeFileName = sessionId + "/" + sensorId + ":"+ freqRange + ".time." + str(startTime)+ "-" + str(seconds) + ".txt"
    if not os.path.exists(util.getPath(STATIC_GENERATED_FILE_LOCATION)  + sessionId):
         os.mkdir(util.getPath(STATIC_GENERATED_FILE_LOCATION)  + sessionId)
    timeFileUrl = Config.getGeneratedDataPath() + "/" + timeFileName
    timeFilePath = util.getPath(STATIC_GENERATED_FILE_LOCATION)  +  timeFileName
    timeFile = open(timeFilePath,"w")
    tm = None
    timeSinceStart = 0
    try:
        for dataMessage in cur:
            del dataMessage["_id"]
            print dumps(dataMessage,indent = 4)
            nM = DataMessage.getNumberOfMeasurements(dataMessage)
            td = DataMessage.getMeasurementDuration(dataMessage)
            tm = DataMessage.getTimePerMeasurement(dataMessage)
            occupancyEndTime = dataMessage[TIME]
            occupancyStartTime = occupancyEndTime - nM*tm
            occupancyData = msgutils.getOccupancyData(dataMessage)
            secondsPerEntry = float(td)/float(nM)
             
            if startTime <= occupancyStartTime and endTime >= occupancyEndTime:
                sindex = 0
                findex = nM
            elif startTime >occupancyStartTime and endTime < occupancyEndTime:
                sindex = int ((startTime - occupancyStartTime)/secondsPerEntry)
                findex = nM -  (occupancyEndTime - endTime)/secondsPerEntry
            elif startTime >= occupancyStartTime:
                print "Case 3 ", startTime, occupancyStartTime
                sindex = int ((startTime - occupancyStartTime)/secondsPerEntry)
                findex = nM
            elif endTime <= occupancyEndTime:
                sindex = 0
                findex = nM -  (occupancyEndTime - endTime)/secondsPerEntry
            timeSinceStart = timeSinceStart + sindex*tm
            print "sindex/findex", sindex,findex
            for i in range(sindex,findex):
                occupancy = str(occupancyData[i])
                occupancyFile.write(occupancy+"\n") 
            for i in range (sindex,findex) :
                timeFile.write(timeSinceStart + "\n")
                timeSinceStart = timeSinceStart + tm
        occupancyFile.close()
        timeFile.close()
        return {STATUS: "OK", OCCUPANCY_FILE_URL:occupancyFileUrl, TIME_FILE_URL:timeFileUrl}

    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
    finally:
         occupancyFile.close()

def getStreamingCaptureOccupancies(sensorId,sys2detect,minFreq,maxFreq,startDate,timeOfDay,seconds,sessionId):

    freqRange = msgutils.freqRange(sys2detect,minFreq,maxFreq)
    dataMessages = DbCollections.getDataMessages(sensorId)
    dataMessage = dataMessages.find_one({})
    if dataMessages == None:
        return {STATUS:"NOK", STATUS_MESSAGE: "No Data Found"}
    locationMessage = msgutils.getLocationMessage(dataMessage)
    timeString = startDate + " " + timeOfDay
    startTime = timezone.parseTime(timeString,locationMessage[TIME_ZONE_KEY])
    endTime = startTime + seconds
    query = {SENSOR_ID:sensorId,FREQ_RANGE:freqRange, "$and":[ {TIME:{"$gte":startTime}}, {TIME:{"$lte":endTime}}]}
    print query
    cur = dataMessages.find(query)
    if cur == None or cur.count() == 0:
    	return {STATUS:"NOK", STATUS_MESSAGE: "No Data Found"}
    occupancyFileName = sessionId + "/" + sensorId + ":" + freqRange + ".occupancy." + str(startTime)+ "-" + str(seconds) + ".txt"
    if not os.path.exists(util.getPath(STATIC_GENERATED_FILE_LOCATION)  + sessionId):
     	os.mkdir(util.getPath(STATIC_GENERATED_FILE_LOCATION)  + sessionId)
    occupancyFileUrl = Config.getGeneratedDataPath() + "/" + occupancyFileName
    occupancyFilePath = util.getPath(STATIC_GENERATED_FILE_LOCATION)  +  occupancyFileName
    occupancyFile = open(occupancyFilePath,"w")
    
    
    timeFileName = sessionId + "/" + sensorId + ":"+ freqRange + ".time." + str(startTime)+ "-" + str(seconds) + ".txt"
    if not os.path.exists(util.getPath(STATIC_GENERATED_FILE_LOCATION)  + sessionId):
         os.mkdir(util.getPath(STATIC_GENERATED_FILE_LOCATION)  + sessionId)
    timeFileUrl = Config.getGeneratedDataPath() + "/" + timeFileName
    timeFilePath = util.getPath(STATIC_GENERATED_FILE_LOCATION)  +  timeFileName
    timeFile = open(timeFilePath,"w")
    
    
    spectrumsPerFrame = None
    streamingFilter = None
    tm = None
    timeSinceStart = 0
    try:
        for dataMessage in cur:
            del dataMessage["_id"]
            print dumps(dataMessage,indent = 4)
            nM = DataMessage.getNumberOfMeasurements(dataMessage)
            td = DataMessage.getMeasurementDuration(dataMessage)
            tm = DataMessage.getTimePerMeasurement(dataMessage)
            occupancyEndTime = dataMessage[TIME]
            occupancyStartTime = occupancyEndTime - nM*tm
            occupancyData = msgutils.getOccupancyData(dataMessage)
            secondsPerEntry = float(td)/float(nM)
             
            if startTime <= occupancyStartTime and endTime >= occupancyEndTime:
             	sindex = 0
            	findex = nM
            elif startTime >occupancyStartTime and endTime < occupancyEndTime:
            	sindex = (startTime - occupancyStartTime)/secondsPerEntry
            	findex = nM -  (occupancyEndTime - endTime)/secondsPerEntry
            elif startTime >= occupancyStartTime:
            	sindex = (startTime - occupancyStartTime)/secondsPerEntry
            	findex = nM
            elif endTime <= occupancyEndTime:
            	sindex = 0
            	findex = nM -  (occupancyEndTime - endTime)/secondsPerEntry
            timeSinceStart = timeSinceStart + sindex*tm
            print "sindex/findex", sindex,findex
            for i in range(sindex,findex):
                occupancy = str(occupancyData[i])
                occupancyFile.write(occupancy+"\n") 
            for i in range (sindex,findex) :
                timeFile.write(timeSinceStart + "\n")
                timeSinceStart = timeSinceStart + tm
        occupancyFile.close()
        timeFile.close()
        return {STATUS: "OK", OCCUPANCY_FILE_URL:occupancyFileUrl, TIME_FILE_URL:timeFileUrl}

    except:
    	print "Unexpected error:", sys.exc_info()[0]
    	print sys.exc_info()
    	traceback.print_exc()
        util.logStackTrace(sys.exc_info())
    finally:
     	occupancyFile.close()
    
        

                

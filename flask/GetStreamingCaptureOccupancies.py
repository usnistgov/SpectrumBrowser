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

from Defines import CHANNEL_COUNT

from Defines import URL


def getStreamingCaptureOccupancies(sensorId,sys2detect,minFreq,maxFreq,startTime,seconds,sessionId):

    freqRange = msgutils.freqRange(sys2detect,minFreq,maxFreq)
    dataMessages = DbCollections.getDataMessages(sensorId)
    endTime = startTime + seconds
    query = {SENSOR_ID:sensorId,FREQ_RANGE:freqRange, TIME:{"$gte":startTime}, TIME:{"$lte":endTime}}
    print query
    cur = dataMessages.find(query)
    if cur == None or cur.count() == 0:
    	return {STATUS:"NOK", STATUS_MESSAGE: "No Data Found"}
    occupancyFileName = sessionId + "/" + sensorId + freqRange + ".occupancy." + str(startTime)+ "-" + str(seconds) + ".txt"
    if not os.path.exists(util.getPath(STATIC_GENERATED_FILE_LOCATION)  + sessionId):
     	os.mkdir(util.getPath(STATIC_GENERATED_FILE_LOCATION)  + sessionId)
    occupancyFileUrl = Config.getGeneratedDataPath() + "/" + occupancyFileName
    occupancyFilePath = util.getPath(STATIC_GENERATED_FILE_LOCATION)  +  occupancyFileName
    occupancyFile = open(occupancyFilePath,"w")
    spectrumsPerFrame = None
    streamingFilter = None
    tm = None
    try:
        for dataMessage in cur:
            if not OCCUPANCY_KEY in dataMessage:
                return {STATUS:"NOK", STATUS_MESSAGE: "No Data Found"}
            del dataMessage["_id"]
            print dumps(dataMessage,indent = 4)
            occupancyCount = dataMessage[OCCUPANCY_VECTOR_LENGTH]
            spectrumsPerFrame = dataMessage[SPECTRUMS_PER_FRAME]
            streamingFilter = dataMessage[STREAMING_FILTER]
            tm = DataMessage.getTimePerMeasurement(dataMessage)
            channelCount = DataMessage.getNumberOfFrequencyBins(dataMessage)
            occupancyStartTime = dataMessage[OCCUPANCY_START_TIME]
            occupancyEndTime = dataMessage[TIME]
            occupancyData = msgutils.getOccupancyData(dataMessage)
            secondsPerEntry = (occupancyEndTime - occupancyStartTime)/occupancyCount
            
            
            if startTime <= occupancyStartTime and endTime >= occupancyEndTime:
             	sindex = 0
            	findex = occupancyCount
            elif startTime >occupancyStartTime and endTime < occupancyEndTime:
            	sindex = (startTime - occupancyStartTime)/secondsPerEntry
            	findex = occupancyCount -  (occupancyEndTime - endTime)/secondsPerEntry
            elif startTime >= occupancyStartTime:
            	sindex = (startTime - occupancyStartTime)/secondsPerEntry
            	findex = occupancyCount
            elif endTime <= occupancyEndTime:
            	sindex = 0
            	findex = occupancyCount -  (occupancyEndTime - endTime)/secondsPerEntry
            print sindex,findex
            for i in range(sindex,findex):
                occupancy = str(occupancyData[i])
                occupancyFile.write(occupancy+"\n")  
        return {STATUS: "OK", URL:occupancyFileUrl, SPECTRUMS_PER_FRAME: spectrumsPerFrame,\
				  TIME_PER_MEASUREMENT: tm, STREAMING_FILTER: streamingFilter, \
				  CHANNEL_COUNT:channelCount}

    except:
    	print "Unexpected error:", sys.exc_info()[0]
    	print sys.exc_info()
    	traceback.print_exc()
        util.logStackTrace(sys.exc_info())
    finally:
     	occupancyFile.close()
    
        

                

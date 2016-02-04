import DbCollections
from Defines import SENSOR_ID
from Defines import OK,NOK
from Defines import SECONDS_PER_DAY
from Defines import SENSOR_KEY
from Defines import STATUS
from Defines import TIME_ZONE_KEY
import timezone
import msgutils
import pymongo



def insertEvent(sensorId,captureEvent):
    """
    Insert an event in the capture database.
    """
    locationMessage = msgutils.getLocationMessage(captureEvent)
    if locationMessage == None:
	return {STATUS:NOK,"ErrorMessage":"Location message not found"}
    tZId = locationMessage[TIME_ZONE_KEY]
    del captureEvent[SENSOR_KEY]
    captureDb = DbCollections.getCaptureEventDb(sensorId)
    captureTime = captureEvent["t"]
    captureEvent["formattedTimeStamp"] = timezone.formatTimeStampLong(captureTime, tZId)
    captureDb.ensure_index([('t', pymongo.DESCENDING)])
    captureDb.insert(captureEvent)
    return {STATUS:OK}

def deleteEvent(sensorId,eventTime):
    captureDb = DbCollections.getCaptureEventDb(sensorId)
    query = {SENSOR_ID:sensorId,"t":eventTime}
    captureDb.remove(query)
    return {STATUS:OK}

def getEvents(sensorId,startTime,days):
    endTime = startTime + days*SECONDS_PER_DAY
    captureDb = DbCollections.getCaptureEventDb(sensorId)
    if startTime > 0:
    	query = {"t":{"$gte":startTime}, "t":{"$lte":endTime}}
    else:
	query = {}
	captureEvent = captureDb.find_one()
	if captureEvent == None:
		return {STATUS:OK,"events":[]}
        locationMessage = msgutils.getLocationMessage(captureEvent)
	if locationMessage == None:
		return {STATUS:NOK,"ErrorMessage":"Location message not found"}
	timeStamp = captureEvent['t']
        tZId = locationMessage[TIME_ZONE_KEY]
        startTime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(timeStamp, tZId)
	endTime = startTime + days*SECONDS_PER_DAY
    	query = {"t":{"$gte":startTime}, "t":{"$lte":endTime}}
	
    found  = captureDb.find(query)
    retval = []
    if found != None:
	for value in found:
		del value["_id"]
		retval.append(value)

    return {STATUS:OK,"events":retval}


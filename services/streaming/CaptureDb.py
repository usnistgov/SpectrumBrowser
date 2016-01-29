import DbCollections
from Defines import SENSOR_ID
from Defines import OK
from Defines import SECONDS_PER_DAY
from Defines import SENSOR_KEY
from Defines import STATUS
import timezone



def insertEvent(sensorId,captureEvent):
    """
    Insert an event in the capture database.
    """
    del captureEvent[SENSOR_KEY]
    captureDb = DbCollections.getCaptureEventDb(sensorId)
    captureDb.insert(captureEvent)
    return {STATUS:OK}

def deleteEvent(sensorId,eventTime):
    captureDb = DbCollections.getCaptureEventDb(sensorId)
    query = {SENSOR_ID:sensorId,"t":eventTime}
    captureDb.remove(query)
    return {STATUS:OK}

def getEvents(sensorId,startTime,days):
    endTime = startTime + days*SECONDS_PER_DAY
    query = {"t":{"$gte":startTime}, "t":{"$lte":endTime}}
    captureDb = DbCollections.getCaptureEventDb(sensorId)
    found  = captureDb.find(query)
    retval = []
    if found != None:
	for value in found:
		del value["_id"]
		retval.append(value)

    return {STATUS:OK,"events":retval}


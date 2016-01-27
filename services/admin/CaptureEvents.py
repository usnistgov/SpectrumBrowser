import DbCollections
import SensorDb
from Defines import SENSOR_ID
from Defines import STATUS

def getCaptureEvents():
	retval = {}
	captureEventCount = {}
	for sensorId in SensorDb.getAllSensorIds():
		captureEvent = DbCollections.getCaptureEventsDb().find({SENSOR_ID:sensorId})
		if captureEvent == None:
		   captureEventCount[sensorId] = 0
		else:
		   captureEventCount[sensorId] = captureEvent.count()
	retval[STATUS] = "OK"
	retval["captureEventCount"] = captureEventCount
	return retval
	

	

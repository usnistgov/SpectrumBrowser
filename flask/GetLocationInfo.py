import timezone
import sets
import util
import sys
import traceback
import DbCollections
from Defines import SENSOR_ID,TIME_ZONE_KEY,SENSOR_KEY
import json

def getLocationInfo():
    """
    Get all the location and system messages that we know about.
    """
    util.debugPrint("getLocationInfo")
    try:
        cur = DbCollections.getLocationMessages().find({})
        cur.batch_size(20)
        retval = {}
        locationMessages = []
        sensorIds = sets.Set()
        for c in cur:
            (c["tStartLocalTime"], c["tStartLocalTimeTzName"]) = timezone.getLocalTime(c["t"], c[TIME_ZONE_KEY])
            del c["_id"]
            del c[SENSOR_KEY]
            locationMessages.append(c)
            sensorIds.add(c[SENSOR_ID])
        retval["locationMessages"] = locationMessages
        systemMessages = []
        for sensorId in sensorIds:
            systemMessage = DbCollections.getSystemMessages().find_one({SENSOR_ID:sensorId})
            del systemMessage["_id"]
            del systemMessage[SENSOR_KEY]
            systemMessages.append(systemMessage)
        retval["systemMessages"] = systemMessages
    except :
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise
    return retval

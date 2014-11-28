import flaskr as main
import timezone
import sets
import util



def getLocationInfo():
    """
    Get all the location and system messages that we know about.
    """
    util.debugPrint("getLocationInfo")
    cur = main.db.locationMessages.find({})
    cur.batch_size(20)
    retval = {}
    locationMessages = []
    sensorIds = sets.Set()
    for c in cur:
        (c["tStartLocalTime"], c["tStartLocalTimeTzName"]) = timezone.getLocalTime(c["t"], c[main.TIME_ZONE_KEY])
        del c["_id"]
        del c["SensorKey"]
        locationMessages.append(c)
        sensorIds.add(c[main.SENSOR_ID])
    retval["locationMessages"] = locationMessages
    systemMessages = []
    for sensorId in sensorIds:
        systemMessage = main.db.systemMessages.find_one({main.SENSOR_ID:sensorId})
        del systemMessage["_id"]
        del systemMessage["SensorKey"]
        systemMessages.append(systemMessage)
    retval["systemMessages"] = systemMessages
    return retval

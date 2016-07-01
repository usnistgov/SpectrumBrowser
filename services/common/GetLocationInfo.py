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


import timezone
import sets
import util
import sys
import traceback
import DbCollections
from Defines import SENSOR_ID, TIME_ZONE_KEY, SENSOR_KEY
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
            (c["tStartLocalTime"], c["tStartLocalTimeTzName"]
             ) = timezone.getLocalTime(c["t"], c[TIME_ZONE_KEY])
            del c["_id"]
            locationMessages.append(c)
            sensorIds.add(c[SENSOR_ID])
        retval["locationMessages"] = locationMessages
        systemMessages = []
        for sensorId in sensorIds:
            systemMessage = DbCollections.getSystemMessages().find_one(
                {SENSOR_ID: sensorId})
            # Issue 139
            if systemMessage != None:
                del systemMessage["_id"]
                systemMessages.append(systemMessage)
        retval["systemMessages"] = systemMessages
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise
    return retval

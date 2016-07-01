#! /usr/local/bin/python2.7
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


import json
import os
import argparse
import Message
from Defines import SYS
from Defines import LOC
from Defines import DATA
import DbCollections
import SensorDb


def upgrade_collection(messages, collection, jsonStringBytes):
    jsonData = json.loads(jsonStringBytes)
    templateKeys = set(jsonData.keys())
    for cur in messages:
        messageKeys = set(cur.keys())
        missingKeys = templateKeys.difference(messageKeys)
        print "missingKeys", str(missingKeys)
        for key in missingKeys:
            defaultValue = jsonData[key]
            print "Updating key : ", key, " Value = ", str(defaultValue)
            cur[key] = defaultValue
        if len(missingKeys) != 0:
            collection.update({"_id": cur["_id"]}, cur)


def upgrade_db(jsonDataStringBytes):
    jsonData = json.loads(jsonStringBytes)
    messageType = Message.getType(jsonData)
    if messageType == SYS:
        messages = DbCollections.getSystemMessages().find()
        collection = DbCollections.getSystemMessages()
        upgrade_collection(messages, collection, jsonStringBytes)
    elif messageType == LOC:
        messages = DbCollections.getLocationMessages().find()
        collection = DbCollections.getLocationMessages()
        upgrade_collection(messages, collection, jsonStringBytes)
    elif messageType == DATA:
        sensorIds = SensorDb.getAllSensorIds()
        for sensorId in sensorIds:
            messages = DbCollections.getDataMessages(sensorId).find()
            collection = DbCollections.getDataMessages(sensorId)
            upgrade_collection(messages, collection, jsonStringBytes)
    else:
        print "unrecognized message type"
        os._exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument('-template', help='Template file for data upgrade')
    args = parser.parse_args()
    templateFileName = args.template
    f = open(templateFileName)
    jsonStringBytes = f.read()
    upgrade_db(jsonStringBytes)
    f.close()
    os._exit(0)

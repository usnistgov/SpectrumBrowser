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

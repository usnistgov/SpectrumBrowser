import json
import os
from pymongo import MongoClient
import argparse


mongodb_host = os.environ.get('DB_PORT_27017_TCP_ADDR', 'localhost')
client = MongoClient(mongodb_host)
db = client.spectrumdb

def upgrade_db(jsonDataString):
    jsonData = json.loads(jsonStringBytes)
    templateKeys = set(jsonData.keys())
    messageType = jsonData["Type"]
    if messageType == "Sys":
        messages = db.systemMessages.find()
        collection = db.systemMessages
    elif messageType == "Loc":
        messages = db.locationMessages.find()
        collection = db.locationMessages
    elif messageType == "Data":
        messages = db.dataMessages.find()
        collection = db.dataMessages
    else:
        print "unrecognized message type"
        os._exit(0)

    for cur in messages:
        messageKeys = set(cur.keys())
        missingKeys = templateKeys.difference(messageKeys)
        print "missingKeys",str(missingKeys)
        for key in missingKeys:
            defaultValue = jsonData[key]
            print "Updating key : ",key, " Value = ", str(defaultValue)
            cur[key] = defaultValue
        if len(missingKeys) != 0:
            collection.update({"_id":cur["_id"]},cur)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument('-template',help='Template file for data upgrade')
    args = parser.parse_args()
    templateFileName = args.template
    f = open(templateFileName)
    jsonStringBytes = f.read()
    upgrade_db(jsonStringBytes)
    f.close()
    os._exit(0)

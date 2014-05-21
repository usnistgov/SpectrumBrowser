import struct
from struct import *
import json
import pymongo
import numpy as np
import os
from os import path
from os import makedirs
from pprint import pprint
from json import JSONEncoder
from pymongo import MongoClient
from pymongo import ASCENDING
from bson.objectid import ObjectId
from bson.json_util import dumps
import gridfs
from datetime import datetime
from dateutil import tz
import calendar
from bson.objectid import ObjectId
import httplib
import argparse
import time



client = MongoClient()
db = client.spectrumdb
bulk = db.spectrumdb.initialize_ordered_bulk_op()
bulk.find({}).remove()




def getLocalTime(utcTime,timeZone):
    to_zone = tz.gettz(timeZone)
    utc = datetime.utcfromtimestamp(utcTime)
    from_zone = tz.gettz('UTC')
    utc = utc.replace(tzinfo=from_zone)
    todatetime = utc.astimezone(to_zone)
    localTime = calendar.timegm(todatetime.timetuple())
    return (localTime,todatetime.tzname())

API_KEY= "AIzaSyDgnBNVM2l0MS0fWMXh3SCzBz6FJyiSodU"
def getLocalTimeZoneFromGoogle(time, lat, long):
    try :
        conn = httplib.HTTPSConnection("maps.googleapis.com")
        conn.request("POST","/maps/api/timezone/json?location="+str(lat)+","+str(long)+"&timestamp="+str(time)+"&sensor=false&key=" + API_KEY,"",{"Content-Length":0})
        res = conn.getresponse()
        if res.status == 200 :
            data = res.read()
            print data
            jsonData = json.loads(data)
            return (jsonData["timeZoneId"],jsonData["timeZoneName"])
        else :
            print "Status ", res.status, res.reason
            return (None,None)
    except:
        return (None,None)


tZoffsets = {"AST": -4 , "EST" : -5, "EDT": -4, "CST" : -6 , "CDT": -5, "MST" : -5, "MDT": -6, "PDT": -7,\
"PST": -8, "AKST" : -9, "HST" : -10, "HAST" : -10, "HADT": -9, "SST" : -11, "SDT" : -10, "CHST": 10}

def getDayBoundaryTimeStamp(timeStamp,timeZoneId):
    import pytz
    try :
        tz = pytz.timezone(timeZoneId)
    except pytz.UnknownTimeZoneError:
        tz = None
    if tz != None :
        dt = datetime.fromtimestamp(float(timeStamp),tz=pytz.timezone(timeZoneId))
        tzName = dt.tzname()
        dt1 = datetime(*dt.timetuple()[:3])
        retval=  calendar.timegm(dt1.timetuple())
        return (retval,tzName)
    else :
        if not timeZoneId in tZoffsets:
            raise Exception("Cant find timeZoneId")
        tZoffset = tZoffsets[timeZoneId]
        dt = datetime.fromtimestamp(float(timeStamp - tZoffset*60*60))
        tzName = dt.tzname()
        dt1 = datetime(*dt.timetuple()[:3])
        retval =  calendar.timegm(dt1.timetuple())
        return (retval,tzName)

def read_data_from_file(filename):
    f = open(filename)
    while True:
        start_time = time.time()
        jsonHeaderLengthStr = f.read(4)
        if jsonHeaderLengthStr == "" :
            print "Done reading file"
            break
        jsonHeaderLength = struct.unpack('i',jsonHeaderLengthStr[0:4])[0]
        jsonStringBytes = f.read(jsonHeaderLength)
        jsonData = json.loads(jsonStringBytes)
        if jsonData['Type'] == "Location" :
            print(json.dumps(jsonData,sort_keys=True, indent=4))
            sensorId = jsonData["sensorID"]
            tInstall = jsonData['tInstall']
            lat = jsonData["Lat"]
            lon = jsonData["Lon"]
            (to_zone,timeZoneName) = getLocalTimeZoneFromGoogle(tInstall,lat,lon)
            # If google returned null, then override with local information
            if to_zone == None:
                to_zone = jsonData["timeZone"]
            else :
                jsonData["timeZone"] = to_zone
            (jsonData["tInstallLocalTime"], jsonData["tInstallLocalTimeTzName"]) = getLocalTime(tInstall,to_zone)
            t = jsonData['t']
            (jsonData['localTime'],jsonData["localTimeTzName"]) = getLocalTime(t,to_zone)
            locationPosts = db.locationMessages
            objectId = locationPosts.insert(jsonData)
            db.locationMessages.ensure_index([('t',pymongo.ASCENDING)])
            post = {"sensorId":sensorId, "id":str(objectId)}
            lastLocationPost = db.lastLocationPostId
            lastLocationPost.update({"sensorId": sensorId}, {"$set":post}, upsert = True)
            end_time = time.time()
            print "Insertion time " + str(end_time-start_time)
        elif jsonData['Type'] == "System" :
            print(json.dumps(jsonData,sort_keys=True, indent=4))
            sensorId = jsonData["sensorID"]
            systemPosts = db.systemMessages
            oid = systemPosts.insert(jsonData)
            db.systemMessages.ensure_index([('t',pymongo.ASCENDING)])
            post = {"sensorId":sensorId, "id":str(oid)}
            lastSystemPostId = db.lastSystemPostId
            lastSystemPostId.update({"sensorId": sensorId}, {"$set":post}, upsert = True)
            end_time = time.time()
            print "Insertion time " + str(end_time-start_time)
        elif jsonData['Type'] == "Data" :
            dataPosts = db.dataMessages
            sensorId = jsonData["sensorID"]
            lastLocationPostId = db.lastLocationPostId.find_one({"sensorId":sensorId})
            lastSystemPostId = db.lastSystemPostId.find_one({"sensorId":sensorId})
            if lastLocationPostId == None or lastSystemPostId == None :
                raise Error("Location post or system post not found for " + sensorId)
            lastSystemPost = db.systemMessages.find_one({"_id": ObjectId(lastSystemPostId["id"])})
            lastLocationPost = db.locationMessages.find_one({"_id":ObjectId(lastLocationPostId["id"])})
            timeZone = lastLocationPost['timeZone']
            (jsonData["localTime"],jsonData["localTimeTzName"]) = getLocalTime(jsonData['t'], timeZone)
            (jsonData["tStartLocalTime"],jsonData["tStartLocalTimeTzName"]) = getLocalTime(jsonData['t1'],timeZone)
            (jsonData['tStartDayBoundaryTimeStamp'],jsonData['tStartDayBoundaryTimeStampTzName']) = getDayBoundaryTimeStamp(jsonData['t'],timeZone)
            #record the location message associated with the data.
            jsonData["locationMessageId"] =  str(lastLocationPost['_id'])
            jsonData["systemMessageId"] = str(lastSystemPost['_id'])
            # prev data message.
            lastSeenDataMessageId = db.lastSeenDataMessageId.find_one({"sensorId":sensorId})
            if lastSeenDataMessageId != None :
                jsonData["prevDataMessageId"] = lastSeenDataMessageId["id"]
            nM = int(jsonData["nM"])
            n = int(jsonData["mPar"]["n"])
            lengthToRead = n*nM
            messageBytes = f.read(lengthToRead)
            fs = gridfs.GridFS(db,jsonData["sensorID"] + "/data")
            key = fs.put(messageBytes)
            jsonData['dataKey'] =  str(key)
            cutoff = jsonData["noiseFloor"] + 2
            db.dataMessages.ensure_index([('t',pymongo.ASCENDING)])
            powerVal = np.array(np.zeros(n*nM))
            occupancyCount=[0 for i in range(0,nM)]
            maxPower = -1000
            minPower = 1000
            if jsonData["mType"] == "FFT-Power" :
                #unpack the power array.
                for i in range(0,lengthToRead):
                    powerVal[i] = struct.unpack('b',messageBytes[i:i+1])[0]
                    maxPower = np.maximum(maxPower,powerVal[i])
                    minPower = np.minimum(minPower,powerVal[i])
                powerArray = powerVal.reshape(nM,n)
                for i in range(0,nM):
                    occupancyCount[i] = float(len(filter(lambda x: x>=cutoff, powerArray[i,:])))/float(n)
            maxOccupancy = float(np.max(occupancyCount))
            meanOccupancy = float(np.mean(occupancyCount))
            minOccupancy = float(np.min(occupancyCount))
            jsonData['meanOccupancy'] = meanOccupancy
            jsonData['maxOccupancy'] = maxOccupancy
            jsonData['minOccupancy'] = minOccupancy
            jsonData['medianOccupancy'] = float(np.median(occupancyCount))
            print json.dumps(jsonData,sort_keys=True, indent=4)
            oid = dataPosts.insert(jsonData)
            #if we have not registered the first data message in the location post, update it.
            if not 'firstDataMessageId' in lastLocationPost :
                lastLocationPost['firstDataMessageId'] = str(oid)
                lastLocationPost['lastDataMessageId'] = str(oid)
                locationPosts.update({"_id": ObjectId(lastLocationPostId["id"])}, {"$set":lastLocationPost}, upsert=False)
            else :
                lastLocationPost['lastDataMessageId'] = str(oid)
                locationPosts.update({"_id": ObjectId(lastLocationPostId["id"])}, {"$set":lastLocationPost}, upsert=False)
            # record the next one in the list so we can easily traverse without searching.
            if  lastSeenDataMessageId != None:
                lastSeenDataMessageId = lastSeenDataMessageId["id"]
                post = dataPosts.find_one({"_id":ObjectId(lastSeenDataMessageId)})
                #link the last data message to the most recent post.
                post["nextDataMessageId"] = str(oid)
                dataPosts.update({"_id": ObjectId(lastSeenDataMessageId)}, {"$set":post}, upsert=False)
            # record the last message seen from this sensor
            post = {"sensorId":sensorId, "id":str(oid)}
            db.lastSeenDataMessageId.update({"sensorId": sensorId},{"$set":post},upsert=True)
            end_time = time.time()
            print "Insertion time " + str(end_time-start_time)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument('-data',help='Filename with readings')
    args = parser.parse_args()
    filename = args.data
    read_data_from_file(filename)



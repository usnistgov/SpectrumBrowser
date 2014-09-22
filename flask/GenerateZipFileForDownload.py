
import flask
from flask import Flask, request,  abort, make_response
from flask import jsonify
import struct
import json
import pymongo
import os
from json import JSONEncoder
from bson.json_util import dumps
from bson.objectid import ObjectId
import urlparse
import gridfs
import ast
import timezone
import populate_db
import sys
import gevent
import sets
import traceback
import zipfile
import flaskr as globals
import util
import msgutils
import zlib
import threading

def generateZipFile(sensorId,startTime,days,minFreq,maxFreq,dumpFileNamePrefix,sessionId):
        util.debugPrint("generateZipFile: " + sensorId + "/" + str(days) + "/" + str(minFreq) + "/" + str(maxFreq) + "/" + sessionId)
        dumpFileName =  sessionId + "/" + dumpFileNamePrefix + ".txt"
        zipFileName = sessionId + "/" + dumpFileNamePrefix + ".zip"
        dumpFilePath = util.getPath("static/generated/") + dumpFileName
        zipFilePath = util.getPath("static/generated/") + zipFileName
        if os.path.exists(dumpFilePath):
            os.remove(dumpFilePath)
        if os.path.exists(zipFilePath):
            os.remove(zipFilePath)
        endTime = int(startTime) + int(days) * globals.SECONDS_PER_DAY
        freqRange = populate_db.freqRange(int(minFreq),int(maxFreq))
        query = {globals.SENSOR_ID:sensorId, "$and": [ {"t": {"$lte":endTime}}, {"t":{"$gte": int(startTime)}}], "freqRange":freqRange }
        firstMessage = globals.db.dataMessages.find_one(query)
        if firstMessage == None:
            util.debugPrint("No data found")
            abort(404)
        locationMessage = msgutils.getLocationMessage(firstMessage)
        if locationMessage == None:
            util.debugPrint("No location info found")
            abort(404)

        systemMessage = globals.db.systemMessages.find_one({globals.SENSOR_ID:sensorId})
        if systemMessage == None:
            debugPrint("No system info found")
            abort(404)

        dumpFile =  open(dumpFilePath,"a")
        zipFile = zipfile.ZipFile(zipFilePath,mode="w")
        try:
            # Write out the system message.
            data = msgutils.getCalData(systemMessage)
            systemMessage["DataType"]="ASCII"
            if "Cal" in systemMessage and systemMessage["Cal"] != "N/A":
                del systemMessage["Cal"]["dataKey"]
            del systemMessage["_id"]
            del systemMessage["SensorKey"]
            systemMessageString = json.dumps(systemMessage, sort_keys=False, indent = 4)
            length = len(systemMessageString)
            dumpFile.write(str(length))
            dumpFile.write("\n")
            dumpFile.write(systemMessageString)
            if data != None:
                dataString = str(data)
                dumpFile.write(dataString)

            # Write out the location message.
            del locationMessage["SensorKey"]
            del locationMessage["_id"]
            del locationMessage["firstDataMessageId"]
            locationMessageString = json.dumps(locationMessage, sort_keys=False, indent = 4)
            locationMessageLength = len(locationMessageString)
            dumpFile.write(str(locationMessageLength))
            dumpFile.write("\n")
            dumpFile.write(locationMessageString)

            # Write out the data messages one at a time
            c = globals.db.dataMessages.find(query)
            for dataMessage in c:
                data = msgutils.getData(dataMessage)
                # delete fields we don't want to export
                del dataMessage["_id"]
                del dataMessage["SensorKey"]
                del dataMessage["locationMessageId"]
                del dataMessage["dataKey"]
                del dataMessage["cutoff"]
                dataMessage["Compression"] = "None"
                dataMessage["DataType"]="ASCII"
                dataMessageString = json.dumps(dataMessage,sort_keys=False, indent=4)
                length = len(dataMessageString)
                dumpFile.write(str(length))
                dumpFile.write("\n")
                dumpFile.write(dataMessageString)
                dumpFile.write(str(data))
            zipFile.write(dumpFilePath,arcname=dumpFileNamePrefix + ".txt", compress_type=zipfile.ZIP_DEFLATED)
            zipFile.close()
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
        finally:
            dumpFile.close()
            os.remove(dumpFilePath)
            zipFile.close()


def generateZipFileForDownload(sensorId,startTime,days,minFreq,maxFreq,sessionId):
    """
    Prepare a zip file for download.
    """
    try:
        dumpFileNamePrefix = "dump-" + sensorId + "." + str(minFreq) + "." + str(maxFreq) + "." + str(startTime) + "." + str(days)
        dumpFileName =  sessionId + "/" + dumpFileNamePrefix + ".txt"
        zipFileName = sessionId + "/" + dumpFileNamePrefix + ".zip"
        dumpFilePath = util.getPath("static/generated/") + dumpFileName
        zipFilePath = util.getPath("static/generated/") + zipFileName
        t = threading.Thread(target=generateZipFile,args=(sensorId,startTime,days,minFreq,maxFreq,dumpFileNamePrefix,sessionId))
        t.daemon = True
        t.start()
        #generateZipFile(sensorId,startTime,days,minFreq,maxFreq,dumpFileNamePrefix,sessionId)
        retval = {"dump":zipFileName}
        return jsonify(retval)
    except:
         print "Unexpected error:", sys.exc_info()[0]
         print sys.exc_info()
         traceback.print_exc()
         raise

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
import sys
import traceback
import zipfile
import util
import msgutils
import threading
import SendMail
import time
import authentication
import struct
import Defines
import DbCollections
import Config
import SessionLock

from multiprocessing import Process

from Defines import SECONDS_PER_DAY
from Defines import SENSOR_ID
from Defines import TYPE
from Defines import USER_NAME
from Defines import BINARY_INT8, BINARY_INT16, BINARY_FLOAT32, ASCII
from Defines import DATA_KEY
from Defines import CAL
from Defines import DATA_TYPE
from Defines import FREQ_RANGE
from Defines import STATUS
from Defines import URL
from Defines import STATIC_GENERATED_FILE_LOCATION


def generateZipFile(sensorId, startTime, days, sys2detect, minFreq, maxFreq,
                    dumpFileNamePrefix, sessionId):
    util.debugPrint("generateZipFile: " + sensorId + "/" + str(days) + "/" +
                    str(minFreq) + "/" + str(maxFreq) + "/" + sessionId)
    dumpFileName = sessionId + "/" + dumpFileNamePrefix + ".txt"
    zipFileName = sessionId + "/" + dumpFileNamePrefix + ".zip"
    dirname = util.getPath(STATIC_GENERATED_FILE_LOCATION + sessionId)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    dumpFilePath = util.getPath(STATIC_GENERATED_FILE_LOCATION) + dumpFileName
    zipFilePath = util.getPath(STATIC_GENERATED_FILE_LOCATION) + zipFileName
    if os.path.exists(dumpFilePath):
        os.remove(dumpFilePath)
    if os.path.exists(zipFilePath):
        os.remove(zipFilePath)
    endTime = int(startTime) + int(days) * SECONDS_PER_DAY
    freqRange = msgutils.freqRange(sys2detect, int(minFreq), int(maxFreq))
    query = {SENSOR_ID: sensorId,
             "t": {"$lte": int(endTime)},
             "t": {"$gte": int(startTime)},
             FREQ_RANGE: freqRange}
    firstMessage = DbCollections.getDataMessages(sensorId).find_one(query)
    if firstMessage is None:
        util.debugPrint("No data found")
        abort(404)
    locationMessage = msgutils.getLocationMessage(firstMessage)
    if locationMessage is None:
        util.debugPrint("generateZipFileForDownload: No location info found")
        return

    systemMessage = DbCollections.getSystemMessages().find_one(
        {SENSOR_ID: sensorId})
    if systemMessage is None:
        util.debugPrint("generateZipFileForDownload : No system info found")
        return

    dumpFile = open(dumpFilePath, "a")
    zipFile = zipfile.ZipFile(zipFilePath, mode="w")
    try:
        # Write out the system message.
        data = msgutils.getCalData(systemMessage)
        systemMessage[DATA_TYPE] = ASCII
        if CAL in systemMessage and DATA_KEY in systemMessage[CAL]:
            del systemMessage[CAL][DATA_KEY]
        del systemMessage["_id"]
        systemMessageString = json.dumps(systemMessage,
                                         sort_keys=False,
                                         indent=4)
        length = len(systemMessageString)
        dumpFile.write(str(length))
        dumpFile.write("\n")
        dumpFile.write(systemMessageString)
        if data is not None:
            dataString = str(data)
            dumpFile.write(dataString)

        # Write out the location message.
        del locationMessage["_id"]
        locationMessageString = json.dumps(locationMessage,
                                           sort_keys=False,
                                           indent=4)
        locationMessageLength = len(locationMessageString)
        dumpFile.write(str(locationMessageLength))
        dumpFile.write("\n")
        dumpFile.write(locationMessageString)

        # Write out the data messages one at a time
        c = DbCollections.getDataMessages(sensorId).find(query)
        for dataMessage in c:
            data = msgutils.getData(dataMessage)
            # delete fields we don't want to export
            del dataMessage["_id"]
            del dataMessage["locationMessageId"]
            del dataMessage[DATA_KEY]
            del dataMessage["cutoff"]
            dataMessage["Compression"] = "None"
            dataMessageString = json.dumps(dataMessage,
                                           sort_keys=False,
                                           indent=4)
            length = len(dataMessageString)
            dumpFile.write(str(length))
            dumpFile.write("\n")
            dumpFile.write(dataMessageString)
            if dataMessage[DATA_TYPE] == ASCII:
                dumpFile.write(str(data))
            elif dataMessage[DATA_TYPE] == BINARY_INT8:
                for dataByte in data:
                    dumpFile.write(struct.pack('b', dataByte))
            elif dataMessage[DATA_TYPE] == BINARY_INT16:
                for dataWord in data:
                    dumpFile.write(struct.pack('i', dataWord))
            elif dataMessage[DATA_TYPE] == BINARY_FLOAT32:
                for dataWord in data:
                    dumpFile.write(struct.pack('f', dataWord))
        zipFile.write(dumpFilePath,
                      arcname=dumpFileNamePrefix + ".txt",
                      compress_type=zipfile.ZIP_DEFLATED)
        zipFile.close()
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
    finally:
        dumpFile.close()
        os.remove(dumpFilePath)
        zipFile.close()
# Watch for the dump file to appear and mail to the user supplied
# email address to notify the user that it is available.


def watchForFileAndSendMail(emailAddress, url, uri):
    """
    Watch for the dump file to appear and send an email to the user
    after it has appeared.
    """
    for i in range(0, 100):
        filePath = util.getPath(STATIC_GENERATED_FILE_LOCATION + uri)
        if os.path.exists(filePath) and os.stat(filePath).st_size != 0:
            message = "This is an automatically generated message.\n"\
            + "The requested data has been generated.\n"\
            + "Please retrieve your data from the following URL: \n"\
            + url \
            + "\nYou must retrieve this file within 24 hours."
            util.debugPrint(message)
            SendMail.sendMail(message, emailAddress,
                              "Your Data Download Request")
            return
        else:
            util.debugPrint("Polling for file " + filePath)
            time.sleep(10)

    message = "This is an automatically generated message.\n"\
    + "Tragically, the requested data could not be generated.\n"\
    + "Sorry to have dashed your hopes into the ground.\n"
    SendMail.sendMail(message, emailAddress, "Your Data Download Request")


def generateSysMessagesZipFile(emailAddress, dumpFileNamePrefix, sensorId,
                               sessionId):
    dumpFileName = sessionId + "/" + dumpFileNamePrefix + ".txt"
    zipFileName = sessionId + "/" + dumpFileNamePrefix + ".zip"
    dirname = util.getPath(STATIC_GENERATED_FILE_LOCATION + sessionId)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    dumpFilePath = util.getPath(STATIC_GENERATED_FILE_LOCATION) + dumpFileName
    zipFilePath = util.getPath(STATIC_GENERATED_FILE_LOCATION) + zipFileName
    if os.path.exists(dumpFilePath):
        os.remove(dumpFilePath)
    if os.path.exists(zipFilePath):
        os.remove(zipFilePath)
    systemMessages = DbCollections.getSystemMessages().find(
        {SENSOR_ID: sensorId})
    if systemMessages is None:
        util.debugPrint("generateZipFileForDownload : No system info found")
        return
    dumpFile = open(dumpFilePath, "a")
    zipFile = zipfile.ZipFile(zipFilePath, mode="w")
    try:
        for systemMessage in systemMessages:
            data = msgutils.getCalData(systemMessage)
            del systemMessage["_id"]
            if CAL in systemMessage and DATA_KEY in systemMessage[CAL]:
                del systemMessage[CAL][DATA_KEY]
            systemMessage[DATA_TYPE] = ASCII
            systemMessageString = json.dumps(systemMessage,
                                             sort_keys=False,
                                             indent=4) + "\n"
            length = len(systemMessageString)
            dumpFile.write(str(length))
            dumpFile.write("\n")
            dumpFile.write(systemMessageString)
            if data is not None:
                dataString = str(data)
                dumpFile.write(dataString)
                dumpFile.write("\n")
        zipFile.write(dumpFilePath,
                      arcname=dumpFileNamePrefix + ".txt",
                      compress_type=zipfile.ZIP_DEFLATED)
        zipFile.close()
        session = SessionLock.getSession(sessionId)
        if session is None:
            os.remove(dumpFilePath)
            os.remove(zipFilePath)
            return
        url = Config.getGeneratedDataPath() + "/" + zipFileName
        watchForFileAndSendMail(emailAddress, url, zipFileName)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
    finally:
        os.remove(dumpFilePath)
        zipFile.close()


def checkForDataAvailability(sensorId, startTime, days, sys2detect, minFreq,
                             maxFreq):
    endTime = int(startTime) + int(days) * SECONDS_PER_DAY
    freqRange = msgutils.freqRange(sys2detect, int(minFreq), int(maxFreq))
    query = {SENSOR_ID: sensorId,
             "t": {"$lte": int(endTime)},
             "t": {"$gte": int(startTime)},
             FREQ_RANGE: freqRange}
    firstMessage = DbCollections.getDataMessages(sensorId).find_one(query)
    if firstMessage is None:
        util.debugPrint("checkForDataAvailability: returning false")
        return False
    else:
        util.debugPrint("checkForDataAvailability: returning true")
        return True


def generateZipFileForDownload(sensorId, startTime, days, sys2detect, minFreq,
                               maxFreq, sessionId):
    """
    Prepare a zip file for download.
    """
    try:
        util.debugPrint("generateZipFileForDownload: " + sensorId + " startTime = " + str(startTime) + \
                         " days " + str(days) + " sys2detect " + sys2detect + " minFreq " + str(minFreq) + \
                         " maxFreq " + str(maxFreq))
        if not checkForDataAvailability(sensorId, startTime, days, sys2detect,
                                        minFreq, maxFreq):
            util.debugPrint("No data found")
            retval = {STATUS: "NOK", "StatusMessage": "No data found"}
        else:
            dumpFileNamePrefix = "dump-" + sensorId + "." + str(
                minFreq) + "." + str(maxFreq) + "." + str(
                    startTime) + "." + str(days)
            zipFileName = sessionId + "/" + dumpFileNamePrefix + ".zip"
            t = threading.Thread(target=generateZipFile,
                                 args=(sensorId, startTime, days, sys2detect,
                                       minFreq, maxFreq, dumpFileNamePrefix,
                                       sessionId))
            t.daemon = True
            t.start()
            url = Config.getGeneratedDataPath() + "/" + zipFileName
            # generateZipFile(sensorId,startTime,days,minFreq,maxFreq,dumpFileNamePrefix,sessionId)
            retval = {STATUS: "OK", "dump": zipFileName, URL: url}
        return retval
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise


def generateSysMessagesZipFileForDownload(sensorId, sessionId):
    util.debugPrint("generateSysMessagesZipFileForDownload")
    systemMessage = DbCollections.getSystemMessages().find_one(
        {SENSOR_ID: sensorId})
    if systemMessage is None:
        return {"status": "NOK", "ErrorMessage": "No data found"}
    else:
        emailAddress = SessionLock.getSession(sessionId)[USER_NAME]
        dumpFilePrefix = "dump-sysmessages-" + sensorId
        zipFileName = sessionId + "/" + dumpFilePrefix + ".zip"
        t = threading.Thread(target=generateSysMessagesZipFile,
                             args=(emailAddress, dumpFilePrefix, sensorId,
                                   sessionId))
        t.daemon = True
        t.start()
        url = Config.getGeneratedDataPath() + "/" + zipFileName
        # generateZipFile(sensorId,startTime,days,minFreq,maxFreq,dumpFileNamePrefix,sessionId)
        return {STATUS: "OK", "dump": zipFileName, URL: url}


def checkForDumpAvailability(uri):
    """
    Check if the dump file (relative to static/generated) is available yet.
    """
    dumpFilePath = util.getPath(STATIC_GENERATED_FILE_LOCATION) + uri

    if not os.path.exists(dumpFilePath):
        return False
    elif os.stat(dumpFilePath).st_size == 0:
        return False
    else:
        size = os.stat(dumpFilePath).st_size
        for i in range(1, 10):
            time.sleep(1)
            newSize = os.stat(dumpFilePath).st_size
            if newSize != size:
                return False
        return True


def emailDumpUrlToUser(emailAddress, url, uri):
    if authentication.isUserRegistered(emailAddress):
        t = threading.Thread(target=watchForFileAndSendMail,
                             args=(emailAddress, url, uri))
        t.daemon = True
        t.start()
        retval = {STATUS: "OK"}
        return retval
    else:
        retval = {STATUS: "NOK"}
        return retval

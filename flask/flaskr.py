from flask import Flask, request, session, g, redirect, url_for, abort
from flask import jsonify
import random
from random import randint
import struct
from struct import *
import json
import pymongo
import numpy as np
import os
from os import path
from pprint import pprint
from json import JSONEncoder
from pymongo import MongoClient
from pymongo import ASCENDING
from bson.json_util import dumps
from bson.objectid import ObjectId
import argparse
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import argparse
import time
import urlparse
import matplotlib.colors as colors
#from mpl_toolkits.axes_grid1 import make_axes_locatable
import gridfs
import ast
import datetime
import pytz
import calendar
import timezone
import png



sessions = {}
secureSessions = {}

app = Flask(__name__,static_url_path="")
random.seed(10)
client = MongoClient()
db = client.spectrumdb
debug = True
SECONDS_PER_DAY = 24*60*60
MILISECONDS_PER_DAY = SECONDS_PER_DAY*1000
UNDER_CUTOFF_COLOR='#D6D6CB'

def checkSessionId(sessionId):
    if debug :
        return True
    elif sessions[request.remote_addr] == None :
        return False
    elif sessions[request.remote_addr] != sessionId :
        return False
    return True

def debugPrint(string):
    if debug :
        print string

######################################################################################
# Internal functions (not exported as web services).
######################################################################################

def generateOccupancyForFFTPower(msg,fileNamePrefix):
    measurementDuration = msg["mPar"]["td"]
    miliSecondsPerMeasurement = float(measurementDuration*1000)/float(nM)
    # Generate the occupancy stats for the acquisition.
    occupancyCount = [0 for i in range(0,nM)]
    for i in range(0,nM):
        occupancyCount[i] = float(len(filter(lambda x: x>=cutoff, spectrogramData[i,:])))/float(n)*100
    timeArray = [i*miliSecondsPerMeasurement for i in range(0,nM)]
    plt.plot(timeArray,occupancyCount,"g.")
    plt.xlabel("Time (Milisec) since start of acquisition")
    plt.ylabel("Channel Occupancy (%)")
    plt.title("Channel Occupancy; Cutoff : " + str(cutoff))
    occupancyFilePath = "static/generated/" + fileNamePrefix + '.occupancy.png'
    plt.savefig(occupancyFilePath)
    plt.close('all')
    return  fileNamePrefix + ".occupancy.png"

def computeDailyMaxMinMeanMedianStats(cursor):
    meanOccupancy = 0
    minOccupancy = 10000
    maxOccupancy = -1
    occupancy = []
    n = 0
    nM = 0
    for msg in cursor:
        fs = gridfs.GridFS(db,msg["sensorID"] + "/occupancy")
        data = fs.get(ObjectId(msg["occupancyKey"])).read()
        occupancyData = ast.literal_eval(data)
        occupancy.append(occupancyData)
        n = msg["mPar"]["n"]
        nM = msg["nM"]
    maxOccupancy = float(np.maximum(occupancy))
    minOccupancy = float(np.minimum(occupancy))
    meanOccupancy = float(np.mean(occupancy))
    medianOccupancy = float(np.median(occupancy))
    return {"maxOccupancy":maxOccupancy, "minOccupancy":minOccupancy, "meanOccupancy":meanOccupancy, "medianOccupancy":medianOccupancy}

def computeDailyMaxMinMeanStats(cursor):
    meanOccupancy = 0
    minOccupancy = 10000
    maxOccupancy = -1
    occupancy = []
    nReadings = cursor.count()
    print "nreadings" , nReadings
    for msg in cursor:
        maxOccupancy = np.maximum(maxOccupancy,msg["maxOccupancy"])
        minOccupancy = np.minimum(minOccupancy,msg["minOccupancy"])
        meanOccupancy = meanOccupancy + msg["meanOccupancy"]
    meanOccupancy = float(meanOccupancy)/float(nReadings)
    return {"maxOccupancy":maxOccupancy, "minOccupancy":minOccupancy, "meanOccupancy":meanOccupancy}

# Generate a spectrogram and occupancy plot for FFTPower data starting at msg.
def generateSingleAcquisitionSpectrogramAndOccupancyForFFTPower(msg,sessionId):
    startTime = msg['t']
    fs = gridfs.GridFS(db,msg["sensorID"] + "/data")
    messageBytes = fs.get(ObjectId(msg["dataKey"])).read()
    debugPrint("Read " + str(len(messageBytes)))
    cutoff = int(request.args.get("cutoff",msg['noiseFloor'] + 2))
    noiseFloor = msg['noiseFloor']
    nM = msg["nM"]
    n = msg["mPar"]["n"]
    measurementDuration = msg["mPar"]["td"]
    miliSecondsPerMeasurement = float(measurementDuration*1000)/float(nM)
    locationMessage = db.locationMessages.find_one({"_id":ObjectId(msg["locationMessageId"])})
    powerVal = np.array(np.zeros(n*nM))
    lengthToRead = n*nM
    # Read the power values
    occupancyCount = 0
    for i in range(0,lengthToRead):
        powerVal[i] = float(struct.unpack('b',messageBytes[i:i+1])[0])
        if powerVal[i] >= cutoff :
            occupancyCount += 1
    occupancy = float(occupancyCount) / float(n*nM)
    spectrogramData = powerVal.reshape(nM,n)

    # generate the spectrogram as an image.
    frame1 = plt.gca()
    frame1.axes.get_xaxis().set_visible(False)
    frame1.axes.get_yaxis().set_visible(False)
    minpower = np.min(powerVal)
    maxpower = np.max(powerVal)
    cmap = plt.cm.spectral
    cmap.set_under(UNDER_CUTOFF_COLOR)
    dirname = "static/generated/" + sessionId
    if not os.path.exists(dirname):
        os.makedirs("static/generated/" + sessionId)
    seconds  = msg['mPar']['td']
    fstop = msg['mPar']['fStop']
    fstart = msg['mPar']['fStart']
    sensorId = msg["sensorID"]
    fig = plt.imshow(np.transpose(spectrogramData),interpolation='none',origin='lower', aspect="auto",vmin=cutoff,vmax=maxpower,cmap=cmap)
    print "Generated fig"
    spectrogramFile =  sessionId + "/" +sensorId + "." + str(startTime) + "." + str(cutoff)
    spectrogramFilePath = "static/generated/" + spectrogramFile
    plt.savefig(spectrogramFilePath + '.png', bbox_inches='tight', pad_inches=0, dpi=100)
    plt.close('all')

    # generate the occupancy data for the measurement.
    occupancyCount = [0 for i in range(0,nM)]
    for i in range(0,nM):
        occupancyCount[i] = float(len(filter(lambda x: x>=cutoff, spectrogramData[i,:])))/float(n)*100
    timeArray = [i*miliSecondsPerMeasurement for i in range(0,nM)]
    # get the size of the generated png.
    reader = png.Reader(filename=spectrogramFilePath + ".png")
    (width,height,pixels,metadata) = reader.read()

    # generate the colorbar as a separate image.
    norm = mpl.colors.Normalize(vmin=cutoff, vmax=maxpower)
    fig = plt.figure(figsize=(4,10))
    ax1 = fig.add_axes([0.0, 0, 0.1, 1])
    cb1 = mpl.colorbar.ColorbarBase(ax1, cmap=cmap, norm=norm, orientation='vertical')
    plt.savefig(spectrogramFilePath + '.cbar.png', bbox_inches='tight', pad_inches=0, dpi=50)
    plt.close('all')

    print msg

    if 'nextDataMessageTime' in msg:
        nextAcquisition = msg['nextDataMessageTime']
    else:
        nextAcquisition = msg['t']

    if 'prevDataMessageTime' in msg:
        prevAcquisition = msg['prevDataMessageTime']
    else:
        prevAcquisition = msg['t']

    result = {"spectrogram": spectrogramFile+".png",                \
            "cbar":spectrogramFile+".cbar.png",                     \
            "maxPower":maxpower,                                    \
            "cutoff":cutoff,                                        \
            "noiseFloor" : noiseFloor,                              \
            "minPower":minpower,                                    \
            "tStartLocalTime": msg["localTime"],                    \
            "timeZone" : locationMessage["localTimeTzName"],        \
            "maxFreq":msg["mPar"]["fStop"],                         \
            "minFreq":msg["mPar"]["fStart"],                        \
            "timeDelta":msg["mPar"]["td"],                          \
            "prevAcquisition" : prevAcquisition ,                   \
            "nextAcquisition" : nextAcquisition ,                   \
            "formattedDate" : timezone.formatTimeStampLong(msg["localTime"], locationMessage["localTimeTzName"]), \
            "image_width":float(width),                             \
            "image_height":float(height)}
    # see if it is well formed.
    print "Computed result"
    debugPrint(result)
    # Now put in the occupancy data
    result["timeArray"] = timeArray
    result["occupancyArray"] = occupancyCount
    return jsonify(result)

# generate the spectrum for a FFT power acquisition at a given milisecond offset.
# from the start time.
def generateSpectrumForFFTPower(msg,milisecOffset,sessionId):
    startTime = msg["t"]
    nM = msg["nM"]
    n = msg["mPar"]["n"]
    measurementDuration = msg["mPar"]["td"]
    miliSecondsPerMeasurement = float(measurementDuration*1000)/float(nM)
    lengthToRead = nM*n
    fs = gridfs.GridFS(db,msg["sensorID"] + "/data")
    messageBytes = fs.get(ObjectId(msg["dataKey"])).read()
    powerVal = np.array(np.zeros(n*nM))
    for i in range(0,lengthToRead):
        powerVal[i] = float(struct.unpack('b',messageBytes[i:i+1])[0])
    spectrogramData = np.transpose(powerVal.reshape(nM,n))
    col = milisecOffset/miliSecondsPerMeasurement
    debugPrint("Col = " + str(col))
    spectrumData = spectrogramData[:,col]
    maxFreq = msg["mPar"]["fStop"]
    minFreq = msg["mPar"]["fStart"]
    nSteps = len(spectrumData)
    freqDelta = float(maxFreq - minFreq)/float(1E6)/nSteps
    freqArray =  [ float(minFreq)/float(1E6) + i*freqDelta for i in range(0,nSteps)]
    plt.scatter(freqArray,spectrumData)
    plt.xlabel("Freq (MHz)")
    plt.ylabel("Power (dBm)")
    locationMessage = db.locationMessages.find_one({"_id": ObjectId(msg["locationMessageId"])})
    localTime = msg["localTime"] + milisecOffset/float(1000)
    tzName = msg["localTimeTzName"]
    plt.title("Spectrum at " + timezone.formatTimeStampLong(localTime,tzName))
    spectrumFile =  sessionId + "/" +msg["sensorID"] + "." + str(startTime) + "." + str(milisecOffset) + ".spectrum.png"
    spectrumFilePath = "static/generated/" + spectrumFile
    plt.savefig(spectrumFilePath, bbox_inches='tight', pad_inches=0, dpi=100)
    plt.close("all")
    retval = {"spectrum" : spectrumFile }
    debugPrint(retval)
    return jsonify(retval)

# Generate power vs. time plot for FFTPower type data.
# given a frequency in MHz
def generatePowerVsTimeForFFTPower(msg,freqMHz,sessionId):
    startTime = msg["t"]
    freqHz = freqMHz * 1E6
    nM = msg["nM"]
    n = msg["mPar"]["n"]
    measurementDuration = msg["mPar"]["td"]
    miliSecondsPerMeasurement = float(measurementDuration*1000)/float(nM)
    lengthToRead = nM*n
    fs = gridfs.GridFS(db,msg["sensorID"] + "/data")
    messageBytes = fs.get(ObjectId(msg["dataKey"])).read()
    powerVal = np.array(np.zeros(n*nM))
    for i in range(0,lengthToRead):
        powerVal[i] = float(struct.unpack('b',messageBytes[i:i+1])[0])
    spectrogramData = np.transpose(powerVal.reshape(nM,n))
    maxFreq = msg["mPar"]["fStop"]
    minFreq = msg["mPar"]["fStart"]
    freqDeltaPerIndex = float(maxFreq - minFreq)/float(n)
    row = int((freqHz - minFreq) / freqDeltaPerIndex )
    debugPrint("row = " + str(row))
    powerValues = spectrogramData[row,:]
    timeArray = [i*miliSecondsPerMeasurement for i in range(0,nM)]
    plt.scatter(timeArray,powerValues)
    plt.title("Power vs. Time at "+ str(freqMHz) + " MHz")
    spectrumFile =  sessionId + "/" +msg["sensorID"] + "." + str(startTime) + "." + str(freqMHz) + ".power.png"
    spectrumFilePath = "static/generated/" + spectrumFile
    plt.xlabel("Time from start of acquistion (milisec)")
    plt.ylabel("Power (dBm)")
    plt.savefig(spectrumFilePath, bbox_inches='tight', pad_inches=0, dpi=100)
    plt.close("all")
    retval = {"powervstime" : spectrumFile }
    debugPrint(retval)
    return jsonify(retval)



######################################################################################

@app.route("/generated/<path:path>",methods=["GET"])
@app.route("/icons/<path:path>",methods=["GET"])
@app.route("/spectrumbrowser/<path:path>",methods=["GET"])
def getScript(path):
    debugPrint("getScript()")
    p = urlparse.urlparse(request.url)
    urlpath = p.path
    return app.send_static_file(urlpath[1:])


@app.route("/", methods=["GET"])
def root():
    debugPrint( "root()" )
    return app.send_static_file("app.html")

@app.route("/spectrumbrowser/getToken",methods=['POST'])
def getToken():
    if not debug:
        sessionId = "guest-" + str(random.randint(1,1000))
    else :
        sessionId = "guest-" + str(123)
    sessions[request.remote_addr] = sessionId
    return jsonify({"status":"OK","sessionId":sessionId})

@app.route("/spectrumbrowser/authenticate/<privilege>/<userName>",methods=['POST'])
def authenticate(privilege,userName):
    p = urlparse.urlparse(request.url)
    query = p.query
    print privilege,userName
    if userName == "guest" and privilege=="user":
       if not debug:
            sessionId = "guest-" +    str(random.randint(1,1000))
       else :
            sessionId = "guest-" +    str(123)
       sessions[request.remote_addr] = sessionId
       return jsonify({"status":"OK","sessionId":sessionId}), 200
    elif query == "" :
       return jsonify({"status":"NOK","sessionId":"0"}), 401
    else :
       q = urlparse.parse_qs(query,keep_blank_values=True)
       # TODO deal with actual logins consult user database etc.
       return jsonify({"status":"NOK","sessionId":sessionId}), 401


@app.route("/spectrumbrowser/getLocationInfo/<sessionId>", methods=["POST"])
def getLocationInfo(sessionId):
    print "gegtLocationInfo"
    if not checkSessionId(sessionId):
        abort(404)
    queryString = "db.locationMessages.find({})"
    debugPrint(queryString)
    cur = eval(queryString)
    cur.batch_size(20)
    retval = "{\"locationMessages\":["
    for c in cur:
        retval = retval + dumps(c,sort_keys=True,indent=4) +","
    retval = retval[:-1] + "]}"
    print retval
    #check to make sure that the json is well formatted.
    if debug:
        json.loads(retval)
    return retval,200

@app.route("/spectrumbrowser/getDailyMaxMinMeanStats/<sensorId>/<startTime>/<dayCount>/<sessionId>", methods=["POST"])
def getDailyStatistics(sensorId, startTime, dayCount, sessionId):
    if not checkSessionId(sessionId):
        abort(404)
    tstart = int(startTime)
    ndays = int(dayCount)
    queryString = { "sensorID" : sensorId, "t" : {'$gte':tstart,'$lte': tstart + SECONDS_PER_DAY}}
    startMessage =  db.dataMessages.find_one(queryString)
    tmin = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(startMessage['t'])
    locationMessage = db.locationMessages.find_one({"_id":ObjectId(startMessage["locationMessageId"])})
    tZId = locationMessage["timeZone"]
    print "tmin = " , tmin, tstart
    result = {}
    values = {}
    for day in range(0,ndays):
        tstart = tmin +  day*SECONDS_PER_DAY
        tend = tstart + SECONDS_PER_DAY
        queryString = { "sensorID" : sensorId, "t" : {'$gte':tstart,'$lte': tend}}
        cur = db.dataMessages.find(queryString)
        cur.batch_size(20)
        dailyStat = computeDailyMaxMinMeanStats(cur)
        values[day*24] = dailyStat
    result["startDate"] = timezone.formatTimeStamp(tmin)
    result["values"] = values
    return jsonify(result)



@app.route("/spectrumbrowser/getDataSummary/<sensorId>/<locationMessageId>/<sessionId>", methods=["POST"])
def getSensorDataDescriptions(sensorId,locationMessageId,sessionId):
    """
    Get the sensor data descriptions for the sensor ID given its location message ID.
    """
    debugPrint( "getSensorDataDescriptions")
    if not checkSessionId(sessionId):
        debugPrint("SessionId not found")
        abort(404)
    locationMessage = db.locationMessages.find_one({"_id":ObjectId(locationMessageId)})
    if locationMessage == None:
        debugPrint("Location Message not found")
        abort(404)
    # tmin and tmax specify the min and the max values of the time range of interest.
    tmin = request.args.get('minTime','')
    tmax = request.args.get('maxTime','')
    tzId = locationMessage["timeZone"]
    if tmin == '' and tmax == '':
        query = { "sensorID": sensorId, "locationMessageId":locationMessageId }
    elif tmin != ''  and tmax == '' :
        mintime = timezone.getDayBoundaryTimeStamp(tmin,tzId)
        query = { "sensorID":sensorId, "locationMessageId":locationMessageId, "t" : {'$gte':mintime} }
    elif tmin == '' and tmax != '':
        maxtime = timezone.getDayBoundaryTimeStamp(tmax,tzId)
        query = { "sensorID":sensorId, "locationMessageId":locationMessageId, "t" : {'$lte':maxtime} }
    else:
        mintime = timezone.getDayBoundaryTimeStamp(tmin,tzId)
        maxtime = timezone.getDayBundaryTimeStamp(tmax,tzId)
        query = { "sensorID": sensorId, "locationMessageId":locationMessageId, "t": { '$lte':maxtime, '$gte':mintime}  }
    debugPrint(query)
    cur = db.dataMessages.find(query)
    if cur == None:
        debugPrint("No data found")
        abort(404)
    nreadings = cur.count()
    if nreadings == 0:
        debugPrint("No data found. zero cur count")
        return jsonify({"readingsCount":float(0)})
    debugPrint("retrieved " + str(nreadings))
    cur.batch_size(20)
    minOccupancy = 10000
    maxOccupancy = -10000
    maxFreq = 0
    minFreq = -1
    meanOccupancy = 0
    minTime = time.time() + 10000
    minLocalTime = time.time() + 10000
    maxTime = 0
    maxLocalTime = 0
    measurementType = "UNDEFINED"
    lastMessage = None
    tStartDayBoundary = 0
    tStartLocalTimeTzName = None
    for msg in cur:
        if tStartDayBoundary == 0 :
            tStartDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg["t"])
            tStartLocalTimeTzName = msg["localTimeTzName"]
            minLocalTime = msg["localTime"]
        minOccupancy = np.minimum(minOccupancy,msg["minOccupancy"])
        maxOccupancy = np.maximum(maxOccupancy,msg["maxOccupancy"])
        maxFreq = np.maximum(msg["mPar"]["fStop"],maxFreq)
        if minFreq == -1 :
            minFreq = msg["mPar"]["fStart"]
        else:
            minFreq = np.minimum(msg["mPar"]["fStart"],minFreq)
        meanOccupancy += msg["meanOccupancy"]
        minTime = np.minimum(minTime,msg["t"])
        maxTime = np.maximum(maxTime,msg["t"])
        measurementType = msg["mType"]
        lastMessage = msg
    tEndReadingsLocalTime = lastMessage["localTime"]
    tEndDayBoundary = endDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg["t"])
    tEndReadingsLocalTimeTzName = lastMessage["localTimeTzName"]
    meanOccupancy = meanOccupancy/nreadings
    return jsonify({"minOccupancy":minOccupancy,                    \
        "tStartReadings":minTime,                                   \
        "tStartLocalTime": minLocalTime,                            \
        "tStartLocalTimeTzName" : tStartLocalTimeTzName,            \
        "tStartDayBoundary":float(tStartDayBoundary),               \
        "tEndReadings":float(maxTime),                              \
        "tEndReadingsLocalTime":float(tEndReadingsLocalTime),       \
        "tEndReadingsLocalTimeTzName" : tEndReadingsLocalTimeTzName, \
        "tEndDayBoundary":float(tEndDayBoundary),                   \
        "maxOccupancy":maxOccupancy,                                \
        "meanOccupancy":meanOccupancy,                              \
        "maxFreq":maxFreq,                                          \
        "minFreq":minFreq,                                          \
        "measurementType": measurementType,                         \
        "readingsCount":float(nreadings)})



@app.route("/spectrumbrowser/getOneDayStats/<sensorId>/<startTime>/<sessionId>", methods=["POST"])
def getOneDayStats(sensorId,startTime,sessionId):
    """
    Get the statistics for a given sensor given a start time for a single day of data.
    The time is rounded to the start of the day boundary.
    """
    mintime = int(startTime)
    maxtime = mintime + SECONDS_PER_DAY
    query = { "sensorID": sensorId,  "t": { '$lte':maxtime, '$gte':mintime}  }
    debugPrint(query)
    msg =  db.dataMessages.find_one(query)
    mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg["t"])
    maxtime = mintime + SECONDS_PER_DAY
    query = { "sensorID": sensorId,  "t": { '$lte':maxtime, '$gte':mintime}  }
    cur = db.dataMessages.find(query)
    if cur == None:
        abort(404)
    res = {}
    values = {}
    query = { "_id": ObjectId(msg["locationMessageId"]) }
    locationMessage = db.locationMessages.find_one(query)
    (localTime, tzName) = timezone.getLocalTime(mintime,locationMessage["timeZone"])
    res["formattedDate"] = timezone.formatTimeStampLong(mintime,tzName)
    for msg in cur:
        values[(msg["t"]-mintime)] = {"t": msg["t"], \
                        "maxOccupancy":msg["maxOccupancy"],\
                        "minOccupancy":msg["minOccupancy"],\
                        "meanOccupancy":msg["meanOccupancy"],\
                        "medianOccupancy":msg["medianOccupancy"]}
    res["values"] = values
    return jsonify(res)


@app.route("/spectrumbrowser/generateSingleAcquisitionSpectrogramAndOccupancy/<sensorId>/<startTime>/<sessionId>", methods=["POST"])
def generateSingleAcquisitionSpectrogram(sensorId,startTime,sessionId):
    if not checkSessionId(sessionId):
        abort(404)
    startTimeInt = int(startTime)
    query = { "sensorID": sensorId,  "t": startTimeInt  }
    debugPrint(query)
    msg = db.dataMessages.find_one(query)
    if msg == None:
        debugPrint("Data message not found for " + startTime)
        abort(404)
    if msg["mType"] == "FFT-Power":
        return generateSingleAcquisitionSpectrogramAndOccupancyForFFTPower(msg,sessionId)
    else:
        debugPrint ("Only FFT Power is supported at present")
        abort(404)


@app.route("/spectrumbrowser/generateSpectrum/<sensorId>/<startTime>/<timeOffset>/<sessionId>", methods=["POST"])
def generateSpectrum(sensorId,startTime,timeOffset,sessionId):
    if not checkSessionId(sessionId):
        abort(404)
    msg = db.dataMessages.find_one({"sensorID":sensorId,"t":int(startTime)})
    if msg == None:
        debugPrint("Error : dataMessage not found " + dataMessageOid)
        abort(404)
    if msg["mType"] == "FFT-Power":
        milisecOffset = int(timeOffset)
        return generateSpectrumForFFTPower(msg,milisecOffset,sessionId)
    else :
        debugPrint("Not implemented yet")
        abort(500)


@app.route("/spectrumbrowser/generatePowerVsTime/<sensorId>/<startTime>/<freq>/<sessionId>", methods=["POST"])
def generatePowerVsTime(sensorId,startTime,freq,sessionId):
    if not checkSessionId(sessionId):
        abort(404)
    msg = db.dataMessages.find_one({"sensorID":sensorId,"t":int(startTime)})
    if msg == None:
        debugPrint("Message not found")
        abort(404)
    if msg["mType"] == "FFT-Power":
        freqMHz = int(freq)
        return generatePowerVsTimeForFFTPower(msg,freqMHz,sessionId)
    else:
        debugPrint("Not implemented yet")
        abort(500)


@app.route("/spectrumbrowser/log", methods=["POST"])
def log():
    data = request.data
    print data
    return "OK"

#@app.route("/spectrumbrowser/login", methods=["POST"])
#def login() :
#    sessionId = random.randint(0,1000)
#    returnVal = {}
#    returnVal["status"] = "OK"
#    returnVal["sessionId"] = sessionId
#    secureSessions[request.remote_addr] = sessionId
#    return JSONEncoder().encode(returnVal)


if __name__ == '__main__':
    #app.run('0.0.0.0',debug="True",port=8443,ssl_context='adhoc')
    app.run('localhost',debug="True")

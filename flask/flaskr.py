import flask
from flask import Flask, request,  abort, make_response
from flask import jsonify
import random
from random import randint
import struct
import json
import pymongo
import numpy as np
import os
from json import JSONEncoder
from pymongo import MongoClient
from bson.json_util import dumps
from bson.objectid import ObjectId
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import time
import urlparse
import gridfs
import ast
import pytz
import timezone
import png
import populate_db
import sys
from flask_sockets import Sockets
import gevent
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from io import BytesIO
import binascii
from Queue import Queue




sessions = {}
secureSessions = {}
gwtSymbolMap = {}

#move these to another module
sensordata = {}
lastDataMessage={}
lastdataseen={}

peakDetection = True
launchedFromMain = False
app = Flask(__name__,static_url_path="")
sockets = Sockets(app)
random.seed(10)
mongodb_host = os.environ.get('DB_PORT_27017_TCP_ADDR', 'localhost')
client = MongoClient(mongodb_host)
db = client.spectrumdb
debug = True
HOURS_PER_DAY = 24
MINUTES_PER_DAY = HOURS_PER_DAY*60
SECONDS_PER_DAY = MINUTES_PER_DAY*60
MILISECONDS_PER_DAY = SECONDS_PER_DAY*1000
UNDER_CUTOFF_COLOR='#D6D6DB'
OVER_CUTOFF_COLOR='#000000'
SENSOR_ID = "SensorID"
TIME_ZONE_KEY="timeZone"
SECONDS_PER_FRAME = 0.1


flaskRoot =  os.environ['SPECTRUM_BROWSER_HOME']+ "/flask/"



######################################################################################
# Internal functions (not exported as web services).
######################################################################################



class MyByteBuffer:

    def __init__(self,ws):
        self.ws = ws
        self.queue = Queue()
        self.buf = BytesIO()


    def readFromWebSocket(self):
        dataAscii = self.ws.receive()
        if dataAscii != None:
            data =  binascii.a2b_base64(dataAscii)
            #print data
            if data != None:
                bio = BytesIO(data)
                bio.seek(0)
                self.queue.put(bio)
        return

    def read(self,size):
        val = self.buf.read(size)
        if val == "" :
            if self.queue.empty():
                self.readFromWebSocket()
                self.buf = self.queue.get()
                val = self.buf.read(size)
            else:
                self.buf = self.queue.get()
                val = self.buf.read(size)
        return val

    def readByte(self):
        val = self.read(1)
        retval = struct.unpack(">b",val)[0]
        return retval

    def readChar(self):
        val = self.read(1)
        return val

    def size(self):
        return self.size



def getPath(x):
    if launchedFromMain:
        return x
    else:
        return flaskRoot + x

def formatError(errorStr):
    return jsonify({"Error": errorStr})

# get the data associated with a message.
def getData(msg) :
    fs = gridfs.GridFS(db,msg[SENSOR_ID]+ "/data")
    messageBytes = fs.get(ObjectId(msg["dataKey"])).read()
    nM = msg["nM"]
    n = msg["mPar"]["n"]
    lengthToRead = nM*n
    if msg["DataType"] == "ASCII":
        powerVal = eval(messageBytes)
    elif msg["DataType"] == "Binary - int8":
        powerVal = np.array(np.zeros(n*nM))
        for i in range(0,lengthToRead):
            powerVal[i] = float(struct.unpack('b',messageBytes[i:i+1])[0])
    elif msg["DataType"] == "Binary - int16":
        powerVal = np.array(np.zeros(n*nM))
        for i in range(0,lengthToRead,2):
            powerVal[i] = float(struct.unpack('h',messageBytes[i:i+2])[0])
    elif msg["DataType"] == "Binary - float32":
        powerVal = np.array(np.zeros(n*nM))
        for i in range(0,lengthToRead,4):
            powerVal[i] = float(struct.unpack('f',messageBytes[i:i+4])[0])
    return powerVal


def loadGwtSymbolMap():
    symbolMapDir = getPath("static/WEB-INF/deploy/spectrumbrowser/symbolMaps/")
    files = [ symbolMapDir + f for f in os.listdir(symbolMapDir) if os.path.isfile(symbolMapDir + f) and os.path.splitext(f)[1] == ".symbolMap" ]
    if len(files) != 0:
        symbolMap = files[0]
        symbolMapFile = open(symbolMap)
        lines = symbolMapFile.readlines()
        for line in lines:
            if line[0] == "#":
                continue
            else:
                pieces = line.split(',')
                lineNo = pieces[-2]
                fileName = pieces[-3]
                symbol = pieces[0]
                gwtSymbolMap[symbol] = {"file":fileName, "line" : lineNo}

def decodeStackTrace (stackTrace):
    lines = stackTrace.split()
    for line in lines :
        pieces = line.split(":")
        if pieces[0] in gwtSymbolMap :
            print gwtSymbolMap.get(pieces[0])
            file = gwtSymbolMap.get(pieces[0])["file"]
            lineNo = gwtSymbolMap.get(pieces[0])["line"]
            print file, lineNo,pieces[1]

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

def getMaxMinFreq(msg):
    return (msg["mPar"]["fStop"],msg["mPar"]["fStart"])


def roundTo2DecimalPlaces(value):
    newVal = int(value*100)
    return float(newVal)/float(100)

def roundTo3DecimalPlaces(value):
    newVal = int(value*1000)
    return float(newVal)/float(1000)

def getLocationMessage(msg):
    return db.locationMessages.find_one({SENSOR_ID:msg[SENSOR_ID], "t": {"$lte":msg["t"]}})

def getNextAcquisition(msg):
    query = {SENSOR_ID: msg[SENSOR_ID], "t":{"$gt": msg["t"]}, "freqRange":msg['freqRange']}
    return db.dataMessages.find_one(query)

def getPrevAcquisition(msg):
    query = {SENSOR_ID: msg[SENSOR_ID], "t":{"$lt": msg["t"]},"freqRange":msg["freqRange"]}
    cur =  db.dataMessages.find(query)
    if cur == None or cur.count() == 0:
        return None
    sortedCur = cur.sort('t',pymongo.DESCENDING).limit(10)
    return sortedCur.next()

def getPrevDayBoundary(msg):
    prevMsg = getPrevAcquisition(msg)
    if prevMsg == None:
        locationMessage = getLocationMessage(msg)
        return  timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg['t'],locationMessage[TIME_ZONE_KEY])
    locationMessage = getLocationMessage(prevMsg)
    timeZone = locationMessage[TIME_ZONE_KEY]
    return timezone.getDayBoundaryTimeStampFromUtcTimeStamp(prevMsg['t'],timeZone)

def getNextDayBoundary(msg):
    nextMsg = getNextAcquisition(msg)
    if nextMsg == None:
        locationMessage = getLocationMessage(msg)
        return  timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg['t'],locationMessage[TIME_ZONE_KEY])
    locationMessage = getLocationMessage(nextMsg)
    timeZone = locationMessage[TIME_ZONE_KEY]
    nextDayBoundary =  timezone.getDayBoundaryTimeStampFromUtcTimeStamp(nextMsg['t'],timeZone)
    if debug:
        thisDayBoundary =   timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg['t'],locationMessage[TIME_ZONE_KEY])
        print "getNextDayBoundary: dayBoundary difference ", (nextDayBoundary - thisDayBoundary)/60/60
    return nextDayBoundary

# get minute index offset from given time in seconds.
# startTime is the starting time from which to compute the offset.
def getIndex(time,startTime) :
    return int ( float(time - startTime) / float(60) )


def generateOccupancyForFFTPower(msg,fileNamePrefix):
    measurementDuration = msg["mPar"]["td"]
    nM = msg['nM']
    n = msg['mPar']['n']
    cutoff = msg['cutoff']
    miliSecondsPerMeasurement = float(measurementDuration*1000)/float(nM)
    spectrogramData = getData(msg)
    # Generate the occupancy stats for the acquisition.
    occupancyCount = [0 for i in range(0,nM)]
    for i in range(0,nM):
        occupancyCount[i] = roundTo2DecimalPlaces(float(len(filter(lambda x: x>=cutoff, spectrogramData[i,:])))/float(n)*100)
    timeArray = [i*miliSecondsPerMeasurement for i in range(0,nM)]
    minOccupancy = np.minimum(occupancyCount)
    maxOccupancy = np.maximum(occupancyCount)
    plt.figure(figsize=(6,4))
    plt.axes([0,measurementDuration*1000,minOccupancy,maxOccupancy])
    plt.xlim([0,measurementDuration*1000])
    plt.plot(timeArray,occupancyCount,"g.")
    plt.xlabel("Time (ms) since start of acquisition")
    plt.ylabel("Band Occupancy (%)")
    plt.title("Band Occupancy; Cutoff : " + str(cutoff))
    occupancyFilePath = getPath("static/generated/") + fileNamePrefix + '.occupancy.png'
    plt.savefig(occupancyFilePath)
    plt.clf()
    plt.close()
    #plt.close('all')
    return  fileNamePrefix + ".occupancy.png"

def computeDailyMaxMinMeanMedianStats(cursor):
    meanOccupancy = 0
    minOccupancy = 10000
    maxOccupancy = -1
    occupancy = []
    n = 0
    for msg in cursor:
        occupancy.append(msg['occupancy'])
        n = msg["mPar"]["n"]
        minFreq = msg["mPar"]["fStart"]
        maxFreq = msg["mPar"]["fStop"]
        cutoff = msg["cutoff"]
    maxOccupancy = float(np.max(occupancy))
    minOccupancy = float(np.min(occupancy))
    meanOccupancy = float(np.mean(occupancy))
    medianOccupancy = float(np.median(occupancy))
    retval =  (n, maxFreq,minFreq,cutoff, \
        {"maxOccupancy":roundTo2DecimalPlaces(maxOccupancy), "minOccupancy":roundTo2DecimalPlaces(minOccupancy),\
        "meanOccupancy":roundTo2DecimalPlaces(meanOccupancy), "medianOccupancy":roundTo2DecimalPlaces(medianOccupancy)})
    debugPrint(retval)
    return retval

# Compute the daily max min and mean stats. The cursor starts on a day
# boundary and ends on a day boundary.
def computeDailyMaxMinMeanStats(cursor):
    debugPrint("computeDailyMaxMinMeanStats")
    meanOccupancy = 0
    minOccupancy = 10000
    maxOccupancy = -1
    nReadings = cursor.count()
    print "nreadings" , nReadings
    if nReadings == 0:
        debugPrint ("zero count")
        return None
    for msg in cursor:
        n = msg["mPar"]["n"]
        minFreq = msg["mPar"]["fStart"]
        maxFreq = msg["mPar"]["fStop"]
        cutoff = msg["cutoff"]
        if msg["mType"] == "FFT-Power" :
            maxOccupancy = np.maximum(maxOccupancy,msg["maxOccupancy"])
            minOccupancy = np.minimum(minOccupancy,msg["minOccupancy"])
            meanOccupancy = meanOccupancy + msg["meanOccupancy"]
        else:
            maxOccupancy = np.maximum(maxOccupancy,msg["occupancy"])
            minOccupancy = np.minimum(maxOccupancy,msg["occupancy"])
            meanOccupancy = meanOccupancy + msg["occupancy"]
    meanOccupancy = float(meanOccupancy)/float(nReadings)
    return (n, maxFreq,minFreq,cutoff, \
        {"maxOccupancy":roundTo2DecimalPlaces(maxOccupancy), "minOccupancy":roundTo2DecimalPlaces(minOccupancy),\
        "meanOccupancy":roundTo2DecimalPlaces(meanOccupancy)})

def generateSingleDaySpectrogramAndOccupancyForSweptFrequency(msg,sessionId,startTime,fstart,fstop):
    try :
        locationMessage = getLocationMessage(msg)
        tz =  locationMessage[TIME_ZONE_KEY]
        startTimeUtc = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(startTime,tz)
        startMsg = db.dataMessages.find_one({SENSOR_ID:msg[SENSOR_ID],"t":{"$gte":startTimeUtc},\
                "freqRange":populate_db.freqRange(fstart,fstop)})
        if startMsg == None:
            debugPrint("Not found")
            abort(404)
        if startMsg['t'] - startTimeUtc > SECONDS_PER_DAY:
            debugPrint("Not found - outside day boundary")
            abort(404)

        msg = startMsg
        sensorId = msg[SENSOR_ID]
        noiseFloor = msg["wnI"]
        vectorLength = msg["mPar"]["n"]
        cutoff = int(request.args.get("cutoff",msg['cutoff']))
        spectrogramFile =  sessionId + "/" +sensorId + "." + str(startTimeUtc) + "." + str(cutoff)
        spectrogramFilePath = getPath("static/generated/") + spectrogramFile
        powerVal = np.array([cutoff for i in range(0,MINUTES_PER_DAY*vectorLength)])
        spectrogramData = powerVal.reshape(vectorLength,MINUTES_PER_DAY)
        # artificial power value when sensor is off.
        sensorOffPower = np.transpose(np.array([2000 for i in range(0,vectorLength)]))

        prevMessage = getPrevAcquisition(msg)

        if prevMessage == None:
            debugPrint ("prevMessage not found")
            prevMessage = msg
            prevAcquisition = sensorOffPower
        else:
            prevAcquisitionTime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(prevMessage['t'],tz)
            debugPrint ("prevMessage[t] " + str(prevMessage['t']) + " msg[t] " + str(msg['t']) + " prevDayBoundary " + str(prevAcquisitionTime))
            prevAcquisition = np.transpose(np.array(getData(prevMessage)))
        occupancy = []
        timeArray = []
        maxpower = -1000
        minpower = 1000
        while True:
            data = getData(msg)
            acquisition = np.transpose(np.array(data))
            minpower = np.minimum(minpower,msg['minPower'])
            maxpower = np.maximum(maxpower,msg['maxPower'])
            if prevMessage['t1'] != msg['t1']:
                 # GAP detected so fill it with sensorOff
                print "Gap generated"
                for i in range(getIndex(prevMessage["t"],startTimeUtc),getIndex(msg["t"],startTimeUtc)):
                    spectrogramData[:,i] = sensorOffPower
            elif prevMessage["t"] > startTimeUtc:
                # Prev message is the same tstart and prevMessage is in the range of interest.
                # Sensor was not turned off.
                # fill forward using the prev acquisition.
                for i in range(getIndex(prevMessage['t'],startTimeUtc), getIndex(msg["t"],startTimeUtc)):
                    spectrogramData[:,i] = prevAcquisition
            else :
                # forward fill from prev acquisition to the start time
                # with the previous power value
                for i in range(0,getIndex(msg["t"],startTimeUtc)):
                    spectrogramData[:,i] = prevAcquisition
            colIndex = getIndex(msg['t'],startTimeUtc)
            spectrogramData[:,colIndex] = acquisition
            timeArray.append(float(msg['t'] - startTimeUtc)/float(3600))
            occupancy.append(roundTo2DecimalPlaces(msg['occupancy']))
            prevMessage = msg
            prevAcquisition = acquisition
            msg = getNextAcquisition(msg)
            if msg == None:
                lastMessage = prevMessage
                for i in range(getIndex(prevMessage["t"],startTimeUtc),MINUTES_PER_DAY):
                    spectrogramData[:,i] = sensorOffPower
                break
            elif msg['t'] - startTimeUtc > SECONDS_PER_DAY:
                for i in range(getIndex(prevMessage["t"],startTimeUtc),MINUTES_PER_DAY):
                    spectrogramData[:,i] = prevAcquisition
                lastMessage = prevMessage
                break

        # generate the spectrogram as an image.
        if not os.path.exists(spectrogramFilePath + ".png"):
           fig = plt.figure(figsize=(6,4))
           frame1 = plt.gca()
           frame1.axes.get_xaxis().set_visible(False)
           frame1.axes.get_yaxis().set_visible(False)
           cmap = plt.cm.spectral
           cmap.set_under(UNDER_CUTOFF_COLOR)
           cmap.set_over(OVER_CUTOFF_COLOR)
           dirname = getPath("static/generated/") + sessionId
           if not os.path.exists(dirname):
              os.makedirs(dirname)
           fig = plt.imshow(spectrogramData,interpolation='none',origin='lower', aspect='auto',vmin=cutoff,vmax=maxpower,cmap=cmap)
           print "Generated fig"
           plt.savefig(spectrogramFilePath + '.png', bbox_inches='tight', pad_inches=0, dpi=100)
           plt.clf()
           plt.close()
        else:
           debugPrint("File exists - not generating image")

        debugPrint("FileName : " + spectrogramFilePath + ".png")

        debugPrint("Reading " + spectrogramFilePath + ".png")
        # get the size of the generated png.
        reader = png.Reader(filename=spectrogramFilePath + ".png")
        (width,height,pixels,metadata) = reader.read()

        debugPrint("width = "+ str(width) + " height = "  + str(height) )

        # generate the colorbar as a separate image.
        if not os.path.exists(spectrogramFilePath + ".cbar.png") :
          norm = mpl.colors.Normalize(vmin=cutoff, vmax=maxpower)
          fig = plt.figure(figsize=(4,10))
          ax1 = fig.add_axes([0.0, 0, 0.1, 1])
          mpl.colorbar.ColorbarBase(ax1, cmap=cmap, norm=norm, orientation='vertical')
          plt.savefig(spectrogramFilePath + '.cbar.png', bbox_inches='tight', pad_inches=0, dpi=50)
          plt.clf()
          plt.close()
        else:
          debugPrint(spectrogramFilePath + ".cbar.png" + " exists -- not generating")


        localTime,tzName = timezone.getLocalTime(startTimeUtc,tz)

        # step back for 24 hours.
        prevAcquisitionTime =  getPrevDayBoundary(startMsg)
        nextAcquisitionTime = getNextDayBoundary(lastMessage)


        result = {"spectrogram": spectrogramFile+".png",                \
            "cbar":spectrogramFile+".cbar.png",                     \
            "maxPower":maxpower,                                    \
            "cutoff":cutoff,                                        \
            "noiseFloor" : noiseFloor,                              \
            "minPower":minpower,                                    \
            "tStartTimeUtc": startTimeUtc,                          \
            TIME_ZONE_KEY : tzName,                                    \
            "timeDelta":HOURS_PER_DAY,                              \
            "prevAcquisition" : prevAcquisitionTime ,               \
            "nextAcquisition" : nextAcquisitionTime ,               \
            "formattedDate" : timezone.formatTimeStampLong(startTimeUtc, tz), \
            "image_width":float(width),                             \
            "image_height":float(height)}

        debugPrint(result)
        result["timeArray"] = timeArray
        result["occupancyArray"] = occupancy
        return jsonify(result)
    except  :
         print "Unexpected error:", sys.exc_info()[0]
         raise

# Generate a spectrogram and occupancy plot for FFTPower data starting at msg.
def generateSingleAcquisitionSpectrogramAndOccupancyForFFTPower(msg,sessionId):
    startTime = msg['t']
    fs = gridfs.GridFS(db,msg[SENSOR_ID] + "/data")
    sensorId = msg[SENSOR_ID]
    messageBytes = fs.get(ObjectId(msg["dataKey"])).read()
    debugPrint("Read " + str(len(messageBytes)))
    cutoff = int(request.args.get("cutoff",msg['cutoff']))
    leftBound = float(request.args.get("leftBound",0))
    rightBound = float(request.args.get("rightBound",0))
    spectrogramFile =  sessionId + "/" +sensorId + "." + str(startTime) + "." + str(leftBound) + "." + str(rightBound) +  "." + str(cutoff)
    spectrogramFilePath = getPath("static/generated/") + spectrogramFile
    if leftBound < 0 or rightBound < 0 :
        debugPrint("Bounds to exlude must be >= 0")
        return None
    measurementDuration = msg["mPar"]["td"]
    miliSecondsPerMeasurement = float(measurementDuration*1000)/float(msg['nM'])
    leftColumnsToExclude = int(leftBound/miliSecondsPerMeasurement)
    rightColumnsToExclude = int(rightBound/miliSecondsPerMeasurement)
    if leftColumnsToExclude + rightColumnsToExclude >= msg['nM']:
        debugPrint("leftColumnToExclude " + str(leftColumnsToExclude)  +  " rightColumnsToExclude " + str(rightColumnsToExclude))
        return None
    debugPrint("LeftColumns to exclude "+ str(leftColumnsToExclude) + " right columns to exclude " + str(rightColumnsToExclude))
    noiseFloor = msg['wnI']
    nM = msg["nM"] - leftColumnsToExclude - rightColumnsToExclude
    n = msg["mPar"]["n"]
    locationMessage = getLocationMessage(msg)
    lengthToRead = n*msg["nM"]
    # Read the power values
    power = getData(msg)
    powerVal = power[n*leftColumnsToExclude:lengthToRead - n*rightColumnsToExclude]
    minTime = float(leftColumnsToExclude * miliSecondsPerMeasurement)/float(1000)
    spectrogramData = powerVal.reshape(nM,n)
    # generate the spectrogram as an image.
    if not os.path.exists(spectrogramFilePath + ".png"):
       dirname = getPath("static/generated/") + sessionId
       if not os.path.exists(dirname):
           os.makedirs(getPath("static/generated/") + sessionId)
       fig = plt.figure(figsize=(6,4))
       frame1 = plt.gca()
       frame1.axes.get_xaxis().set_visible(False)
       frame1.axes.get_yaxis().set_visible(False)
       minpower = msg['minPower']
       maxpower = msg['maxPower']
       cmap = plt.cm.spectral
       cmap.set_under(UNDER_CUTOFF_COLOR)
       fig = plt.imshow(np.transpose(spectrogramData),interpolation='none',origin='lower', aspect="auto",vmin=cutoff,vmax=maxpower,cmap=cmap)
       print "Generated fig"
       plt.savefig(spectrogramFilePath + '.png', bbox_inches='tight', pad_inches=0, dpi=100)
       plt.clf()
       plt.close()
    else :
       debugPrint("File exists -- not regenerating")

    # generate the occupancy data for the measurement.
    occupancyCount = [0 for i in range(0,nM)]
    for i in range(0,nM):
        occupancyCount[i] = roundTo2DecimalPlaces(float(len(filter(lambda x: x>=cutoff, spectrogramData[i,:])))/float(n)*100)
    timeArray = [int((i + leftColumnsToExclude)*miliSecondsPerMeasurement)  for i in range(0,nM)]

    # get the size of the generated png.
    reader = png.Reader(filename=spectrogramFilePath + ".png")
    (width,height,pixels,metadata) = reader.read()

    if not os.path.exists(spectrogramFilePath + ".cbar.png"):
       # generate the colorbar as a separate image.
       norm = mpl.colors.Normalize(vmin=cutoff, vmax=maxpower)
       fig = plt.figure(figsize=(4,10))
       ax1 = fig.add_axes([0.0, 0, 0.1, 1])
       mpl.colorbar.ColorbarBase(ax1, cmap=cmap, norm=norm, orientation='vertical')
       plt.savefig(spectrogramFilePath + '.cbar.png', bbox_inches='tight', pad_inches=0, dpi=50)
       plt.clf()
       plt.close()

    nextAcquisition = getNextAcquisition(msg)
    prevAcquisition = getPrevAcquisition(msg)

    if nextAcquisition != None:
        nextAcquisitionTime = nextAcquisition['t']
    else:
        nextAcquisitionTime = msg['t']

    if prevAcquisition != None:
        prevAcquisitionTime = prevAcquisition['t']
    else:
        prevAcquisitionTime = msg['t']

    tz =  locationMessage[TIME_ZONE_KEY]

    timeDelta = msg["mPar"]["td"] - float(leftBound)/float(1000) - float(rightBound)/float(1000)

    result = {"spectrogram": spectrogramFile+".png",                \
            "cbar":spectrogramFile+".cbar.png",                     \
            "maxPower":msg['maxPower'],                             \
            "cutoff":cutoff,                                        \
            "noiseFloor" : noiseFloor,                              \
            "minPower":msg['minPower'],                             \
            "maxFreq":msg["mPar"]["fStop"],                         \
            "minFreq":msg["mPar"]["fStart"],                        \
            "minTime": minTime,                                     \
            "timeDelta": timeDelta,                                 \
            "prevAcquisition" : prevAcquisitionTime ,               \
            "nextAcquisition" : nextAcquisitionTime ,               \
            "formattedDate" : timezone.formatTimeStampLong(msg['t'] + leftBound , tz), \
            "image_width":float(width),                             \
            "image_height":float(height)}
    # see if it is well formed.
    print dumps(result,indent=4)
    # Now put in the occupancy data
    result["timeArray"] = timeArray
    result["occupancyArray"] = occupancyCount
    return jsonify(result)

def generateSpectrumForSweptFrequency(msg,sessionId):
    spectrumData = getData(msg)
    maxFreq = msg["mPar"]["fStop"]
    minFreq = msg["mPar"]["fStart"]
    nSteps = len(spectrumData)
    freqDelta = float(maxFreq - minFreq)/float(1E6)/nSteps
    freqArray =  [ float(minFreq)/float(1E6) + i*freqDelta for i in range(0,nSteps)]
    fig = plt.figure(figsize=(6,4))
    plt.scatter(freqArray,spectrumData)
    plt.xlabel("Freq (MHz)")
    plt.ylabel("Power (dBm)")
    locationMessage = db.locationMessages.find_one({"_id": ObjectId(msg["locationMessageId"])})
    t  = msg["t"]
    tz =  locationMessage[TIME_ZONE_KEY]
    plt.title("Spectrum at " + timezone.formatTimeStampLong(t,tz))
    spectrumFile =  sessionId + "/" +msg[SENSOR_ID] + "." + str(msg['t']) + ".spectrum.png"
    spectrumFilePath = getPath("static/generated/") + spectrumFile
    plt.savefig(spectrumFilePath,  pad_inches=0, dpi=100)
    plt.clf()
    plt.close()
    #plt.close("all")
    retval = {"spectrum" : spectrumFile }
    debugPrint(retval)
    return jsonify(retval)


# generate the spectrum for a FFT power acquisition at a given milisecond offset.
# from the start time.
def generateSpectrumForFFTPower(msg,milisecOffset,sessionId):
    startTime = msg["t"]
    nM = msg["nM"]
    n = msg["mPar"]["n"]
    measurementDuration = msg["mPar"]["td"]
    miliSecondsPerMeasurement = float(measurementDuration*1000)/float(nM)
    powerVal = getData(msg)
    spectrogramData = np.transpose(powerVal.reshape(nM,n))
    col = milisecOffset/miliSecondsPerMeasurement
    debugPrint("Col = " + str(col))
    spectrumData = spectrogramData[:,col]
    maxFreq = msg["mPar"]["fStop"]
    minFreq = msg["mPar"]["fStart"]
    nSteps = len(spectrumData)
    freqDelta = float(maxFreq - minFreq)/float(1E6)/nSteps
    freqArray =  [ float(minFreq)/float(1E6) + i*freqDelta for i in range(0,nSteps)]
    fig = plt.figure(figsize=(6,4))
    plt.scatter(freqArray,spectrumData)
    plt.xlabel("Freq (MHz)")
    plt.ylabel("Power (dBm)")
    locationMessage = db.locationMessages.find_one({"_id": ObjectId(msg["locationMessageId"])})
    t  = msg["t"] + milisecOffset/float(1000)
    tz =  locationMessage[TIME_ZONE_KEY]
    plt.title("Spectrum at " + timezone.formatTimeStampLong(t,tz))
    spectrumFile =  sessionId + "/" +msg[SENSOR_ID] + "." + str(startTime) + "." + str(milisecOffset) + ".spectrum.png"
    spectrumFilePath = getPath("static/generated/") + spectrumFile
    plt.savefig(spectrumFilePath,  pad_inches=0, dpi=100)
    plt.clf()
    plt.close()
    #plt.close("all")
    retval = {"spectrum" : spectrumFile }
    debugPrint(retval)
    return jsonify(retval)

def generatePowerVsTimeForSweptFrequency(msg,freqHz,sessionId):
    (maxFreq,minFreq) = getMaxMinFreq(msg)
    locationMessage = getLocationMessage(msg)
    timeZone = locationMessage[TIME_ZONE_KEY]
    if freqHz > maxFreq:
        freqHz = maxFreq
    if freqHz < minFreq:
        freqHz = minFreq
    n = msg["mPar"]["n"]
    freqIndex = int(float(freqHz-minFreq)/float(maxFreq-minFreq)* float(n))
    powerArray = []
    timeArray = []
    startTime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg['t'],timeZone)
    while True:
        data = getData(msg)
        powerArray.append(data[freqIndex])
        timeArray.append(float(msg['t']-startTime)/float(3600))
        nextMsg = getNextAcquisition(msg)
        if nextMsg == None:
            break
        elif nextMsg['t'] - startTime > SECONDS_PER_DAY:
            break
        else:
            msg = nextMsg

    fig = plt.figure(figsize=(6,4))
    plt.xlim([0,23])
    freqMHz = float(freqHz)/1E6
    plt.title("Power vs. Time at "+ str(freqMHz) + " MHz")
    plt.xlabel("Time from start of day (Hours)")
    plt.ylabel("Power (dBm)")
    plt.xlim([0,23])
    plt.scatter(timeArray,powerArray)
    spectrumFile =  sessionId + "/" +msg[SENSOR_ID] + "." + str(startTime) + "." + str(freqMHz) + ".power.png"
    spectrumFilePath = getPath("static/generated/") + spectrumFile
    plt.savefig(spectrumFilePath,  pad_inches=0, dpi=100)
    plt.clf()
    plt.close()
    #plt.close("all")
    retval = {"powervstime" : spectrumFile }
    debugPrint(retval)
    return jsonify(retval)



# Generate power vs. time plot for FFTPower type data.
# given a frequency in MHz
def generatePowerVsTimeForFFTPower(msg,freqHz,sessionId):
    startTime = msg["t"]
    n = msg["mPar"]["n"]
    leftBound = float(request.args.get("leftBound",0))
    rightBound = float(request.args.get("rightBound",0))
    if leftBound < 0 or rightBound < 0 :
        debugPrint("Bounds to exlude must be >= 0")
        return None
    measurementDuration = msg["mPar"]["td"]
    miliSecondsPerMeasurement = float(measurementDuration*1000)/float(msg['nM'])
    leftColumnsToExclude = int(leftBound/miliSecondsPerMeasurement)
    rightColumnsToExclude = int(rightBound/miliSecondsPerMeasurement)
    if leftColumnsToExclude + rightColumnsToExclude >= msg['nM']:
        debugPrint("leftColumnToExclude " + str(leftColumnsToExclude)  +  " rightColumnsToExclude " + str(rightColumnsToExclude))
        return None
    nM = msg["nM"] - leftColumnsToExclude - rightColumnsToExclude
    power = getData(msg)
    lengthToRead = n*msg["nM"]
    powerVal = power[n*leftColumnsToExclude:lengthToRead - n*rightColumnsToExclude]
    spectrogramData = np.transpose(powerVal.reshape(nM,n))
    maxFreq = msg["mPar"]["fStop"]
    minFreq = msg["mPar"]["fStart"]
    freqDeltaPerIndex = float(maxFreq - minFreq)/float(n)
    row = int((freqHz - minFreq) / freqDeltaPerIndex )
    debugPrint("row = " + str(row))
    if  row < 0 :
        debugPrint("WARNING: row < 0")
        row = 0
    powerValues = spectrogramData[row,:]
    timeArray = [(leftColumnsToExclude + i)*miliSecondsPerMeasurement for i in range(0,nM)]
    fig = plt.figure(figsize=(6,4))
    plt.xlim([leftBound,measurementDuration*1000 - rightBound])
    plt.scatter(timeArray,powerValues)
    freqMHz = float(freqHz)/1E6
    plt.title("Power vs. Time at "+ str(freqMHz) + " MHz")
    spectrumFile =  sessionId + "/" +msg[SENSOR_ID] + "." + str(startTime) + "." + str(leftBound) + "." + str(rightBound) \
        + "."+ str(freqMHz) + ".power.png"
    spectrumFilePath = getPath("static/generated/") + spectrumFile
    plt.xlabel("Time from start of acquistion (ms)")
    plt.ylabel("Power (dBm)")
    plt.savefig(spectrumFilePath,  pad_inches=0, dpi=100)
    plt.clf()
    plt.close()
    #plt.close("all")
    retval = {"powervstime" : spectrumFile }
    debugPrint(retval)
    return jsonify(retval)



######################################################################################

@app.route("/generated/<path:path>",methods=["GET"])
@app.route("/myicons/<path:path>",methods=["GET"])
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
       #q = urlparse.parse_qs(query,keep_blank_values=True)
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
        (c["tStartLocalTime"],c["tStartLocalTimeTzName"]) = timezone.getLocalTime(c["t"],c[TIME_ZONE_KEY])
        retval = retval + dumps(c,sort_keys=True,indent=4) +","
    retval = retval[:-1] + "]}"
    print retval
    #check to make sure that the json is well formatted.
    if debug:
        json.loads(retval)
    return retval,200

@app.route("/spectrumbrowser/getDailyMaxMinMeanStats/<sensorId>/<startTime>/<dayCount>/<fmin>/<fmax>/<sessionId>", methods=["POST"])
def getDailyStatistics(sensorId, startTime, dayCount, fmin, fmax,sessionId):
    debugPrint("getDailyStatistics : " + sensorId + " " + startTime + " " + dayCount )
    if not checkSessionId(sessionId):
        abort(404)
    tstart = int(startTime)
    ndays = int(dayCount)
    fmin = int(fmin)
    fmax = int(fmax)
    queryString = { SENSOR_ID : sensorId, "t" : {'$gte':tstart}, "freqRange": populate_db.freqRange(fmin,fmax)}
    startMessage =  db.dataMessages.find_one(queryString)
    if startMessage == None:
        errorStr = "Start Message Not Found"
        debugPrint(errorStr)
        response = make_response(formatError(errorStr),404)
        return response
    locationMessage = getLocationMessage(startMessage)
    tZId = locationMessage[TIME_ZONE_KEY]
    if locationMessage == None:
        errorStr = "Location Message Not Found"
        debugPrint(errorStr)
        response = make_response(formatError(errorStr),404)
    tmin = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(startMessage['t'],tZId)
    result = {}
    values = {}
    for day in range(0,ndays):
        tstart = tmin +  day*SECONDS_PER_DAY
        tend = tstart + SECONDS_PER_DAY
        queryString = { SENSOR_ID : sensorId, "t" : {'$gte':tstart,'$lte': tend},"freqRange":populate_db.freqRange(fmin,fmax)}
        print queryString
        cur = db.dataMessages.find(queryString)
        cur.batch_size(20)
        if startMessage['mType'] == "FFT-Power":
           stats = computeDailyMaxMinMeanStats(cur)
        else:
           stats = computeDailyMaxMinMeanMedianStats(cur)
        # gap in readings. continue.
        if stats == None:
            continue
        (nChannels,maxFreq,minFreq,cutoff,dailyStat) = stats
        values[day*24] = dailyStat
    result["tmin"] = tmin
    result["maxFreq"] = maxFreq
    result["minFreq"] = minFreq
    result["cutoff"] = cutoff
    result["channelCount"] = nChannels
    result["startDate"] = timezone.formatTimeStampLong(tmin,tZId)
    result["values"] = values
    debugPrint(result)
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
    # min and specifies the freq band of interest. If nothing is specified or the freq is -1,
    #then all frequency bands are queried.
    minFreq = int (request.args.get("minFreq","-1"))
    maxFreq = int(request.args.get("maxFreq","-1"))
    if minFreq != -1 and maxFreq != -1 :
        freqRange = populate_db.freqRange(minFreq,maxFreq)
    else:
        freqRange = None
    # tmin and tmax specify the min and the max values of the time range of interest.
    tmin = request.args.get('minTime','')
    dayCount = request.args.get('dayCount','')
    tzId = locationMessage[TIME_ZONE_KEY]
    if freqRange == None:
        if tmin == '' and dayCount == '':
            query = { SENSOR_ID: sensorId, "locationMessageId":locationMessageId }
        elif tmin != ''  and dayCount == '' :
            mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin),tzId)
            query = { SENSOR_ID:sensorId, "locationMessageId":locationMessageId, "t" : {'$gte':mintime} }
        else:
            mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin),tzId)
            maxtime = mintime + int(dayCount)*SECONDS_PER_DAY
            query = { SENSOR_ID: sensorId, "locationMessageId":locationMessageId, "t": { '$lte':maxtime, '$gte':mintime}  }
    else :
        if tmin == '' and dayCount == '':
            query = { SENSOR_ID: sensorId, "locationMessageId":locationMessageId, "freqRange": freqRange }
        elif tmin != ''  and dayCount == '' :
            mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin),tzId)
            query = { SENSOR_ID:sensorId, "locationMessageId":locationMessageId, "t" : {'$gte':mintime}, "freqRange":freqRange }
        else:
            mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin),tzId)
            maxtime = mintime + int(dayCount)*SECONDS_PER_DAY
            query = { SENSOR_ID: sensorId, "locationMessageId":locationMessageId, "t": { '$lte':maxtime, '$gte':mintime} , "freqRange":freqRange }

    debugPrint(query)
    cur = db.dataMessages.find(query)
    if cur == None:
       errorStr = "No data found"
       response = make_response(formatError(errorStr),404)
       return response
    nreadings = cur.count()
    if nreadings == 0:
        debugPrint("No data found. zero cur count.")
        del query['t']
        msg = db.dataMessages.find_one(query)
        if msg != None:
            tStartDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg["t"],tzId)
            if dayCount == '':
                query["t"] = {"$gte":tStartDayBoundary}
            else:
                maxtime = tStartDayBoundary + int(dayCount)*SECONDS_PER_DAY
                query["t"] = {"$gte":tStartDayBoundary, "$lte":maxtime}
            cur = db.dataMessages.find(query)
            nreadings = cur.count()
        else :
             errorStr = "No data found"
             response = make_response(formatError(errorStr),404)
             return response
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
            tStartDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg["t"],tzId)
            (minLocalTime,tStartLocalTimeTzName) = timezone.getLocalTime(msg['t'],tzId)
        if msg["mType"] == "FFT-Power" :
            minOccupancy = np.minimum(minOccupancy,msg["minOccupancy"])
            maxOccupancy = np.maximum(maxOccupancy,msg["maxOccupancy"])
        else:
            minOccupancy = np.minimum(minOccupancy,msg["occupancy"])
            maxOccupancy = np.maximum(maxOccupancy,msg["occupancy"])
        maxFreq = np.maximum(msg["mPar"]["fStop"],maxFreq)
        if minFreq == -1 :
            minFreq = msg["mPar"]["fStart"]
        else:
            minFreq = np.minimum(msg["mPar"]["fStart"],minFreq)
        if "meanOccupancy" in msg:
            meanOccupancy += msg["meanOccupancy"]
        else:
            meanOccupancy += msg["occupancy"]
        minTime = np.minimum(minTime,msg["t"])
        maxTime = np.maximum(maxTime,msg["t"])
        measurementType = msg["mType"]
        lastMessage = msg
    tz =  locationMessage[TIME_ZONE_KEY]
    (tEndReadingsLocalTime,tEndReadingsLocalTimeTzName) = timezone.getLocalTime(lastMessage['t'],tzId)
    tEndDayBoundary = endDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(lastMessage["t"],tzId)
    # now get the global min and max time of the aquistions.
    if 't' in query:
        del query['t']
    cur = db.dataMessages.find(query)
    firstMessage = cur.next()
    cur = db.dataMessages.find(query)
    sortedCur = cur.sort('t',pymongo.DESCENDING).limit(10)
    lastMessage = sortedCur.next()
    tAquisitionStart = firstMessage['t']
    tAquisitionEnd = lastMessage['t']
    tAquisitionStartFormattedTimeStamp = timezone.formatTimeStampLong(tAquisitionStart,tzId)
    tAquisitionEndFormattedTimeStamp = timezone.formatTimeStampLong(tAquisitionEnd,tzId)
    meanOccupancy = meanOccupancy/nreadings
    retval = {"minOccupancy":minOccupancy,                          \
        "tAquistionStart": tAquisitionStart,                    \
        "tAquisitionStartFormattedTimeStamp": tAquisitionStartFormattedTimeStamp,                    \
        "tAquisitionEnd":tAquisitionEnd, \
        "tAquisitionEndFormattedTimeStamp": tAquisitionEndFormattedTimeStamp,                        \
        "tStartReadings":minTime,                                   \
        "tStartLocalTime": minLocalTime,                            \
        "tStartLocalTimeTzName" : tStartLocalTimeTzName,            \
        "tStartLocalTimeFormattedTimeStamp" : timezone.formatTimeStampLong(minTime,tzId), \
        "tStartDayBoundary":float(tStartDayBoundary),               \
        "tEndReadings":float(maxTime),                              \
        "tEndReadingsLocalTime":float(tEndReadingsLocalTime),       \
        "tEndReadingsLocalTimeTzName" : tEndReadingsLocalTimeTzName, \
        "tEndLocalTimeFormattedTimeStamp" : timezone.formatTimeStampLong(maxTime,tzId), \
        "tEndDayBoundary":float(tEndDayBoundary),                   \
        "maxOccupancy":roundTo2DecimalPlaces(maxOccupancy),          \
        "meanOccupancy":roundTo2DecimalPlaces(meanOccupancy),        \
        "maxFreq":maxFreq,                                          \
        "minFreq":minFreq,                                          \
        "measurementType": measurementType,                         \
        "readingsCount":float(nreadings)}
    print retval
    return jsonify(retval)



@app.route("/spectrumbrowser/getOneDayStats/<sensorId>/<startTime>/<minFreq>/<maxFreq>/<sessionId>", methods=["POST"])
def getOneDayStats(sensorId,startTime,minFreq,maxFreq,sessionId):
    """
    Get the statistics for a given sensor given a start time for a single day of data.
    The time is rounded to the start of the day boundary.
    """
    minFreq = int(minFreq)
    maxFreq = int(maxFreq)
    freqRange = populate_db.freqRange(minFreq,maxFreq)
    mintime = int(startTime)
    maxtime = mintime + SECONDS_PER_DAY
    query = { SENSOR_ID: sensorId,  "t": { '$lte':maxtime, '$gte':mintime}, "freqRange":freqRange  }
    debugPrint(query)
    msg =  db.dataMessages.find_one(query)
    query = { "_id": ObjectId(msg["locationMessageId"]) }
    locationMessage = db.locationMessages.find_one(query)
    mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg["t"],locationMessage[TIME_ZONE_KEY])
    maxtime = mintime + SECONDS_PER_DAY
    query = { SENSOR_ID: sensorId,  "t": { '$lte':maxtime, '$gte':mintime} , "freqRange":freqRange }
    cur = db.dataMessages.find(query)
    if cur == None:
        abort(404)
    res = {}
    values = {}
    res["formattedDate"] = timezone.formatTimeStampLong(mintime,locationMessage[TIME_ZONE_KEY])
    for msg in cur:
        channelCount = msg["mPar"]["n"]
        cutoff = msg["cutoff"]
        values[msg["t"]-mintime] = {"t": msg["t"], \
                        "maxPower" : msg["maxPower"],\
                        "minPower" : msg["minPower"],\
                        "maxOccupancy":roundTo2DecimalPlaces(msg["maxOccupancy"]),\
                        "minOccupancy":roundTo2DecimalPlaces(msg["minOccupancy"]),\
                        "meanOccupancy":roundTo2DecimalPlaces(msg["meanOccupancy"]),\
                        "medianOccupancy":roundTo2DecimalPlaces(msg["medianOccupancy"])}
    res["channelCount"] = channelCount
    res["cutoff"] = cutoff
    res["values"] = values
    return jsonify(res)


@app.route("/spectrumbrowser/generateSingleAcquisitionSpectrogramAndOccupancy/<sensorId>/<startTime>/<minFreq>/<maxFreq>/<sessionId>", methods=["POST"])
def generateSingleAcquisitionSpectrogram(sensorId,startTime,minFreq,maxFreq,sessionId):
    """ Generate the single acquisiton spectrogram or the daily spectrogram.
        sensorId is the sensor ID of interest.
        The start time is a day boundary timeStamp for swept freq.
        The start time is the time stamp for the data message for FFT power. """
    try:
        if not checkSessionId(sessionId):
            abort(404)
        startTimeInt = int(startTime)
        minfreq = int(minFreq)
        maxfreq = int(maxFreq)
        query = { SENSOR_ID: sensorId}
        msg = db.dataMessages.find_one(query)
        if msg == None:
            debugPrint("Sensor ID not found " + sensorId)
            abort(404)
        if msg["mType"] == "FFT-Power":
            query = { SENSOR_ID: sensorId,  "t": startTimeInt, "freqRange": populate_db.freqRange(minfreq,maxfreq)}
            debugPrint(query)
            msg = db.dataMessages.find_one(query)
            if msg == None:
                errorStr = "Data message not found for " + startTime
                debugPrint(errorStr)
                response = make_response(formatError(errorStr),404)
                return response
            result =  generateSingleAcquisitionSpectrogramAndOccupancyForFFTPower(msg,sessionId)
            if result == None:
                errorStr = "Illegal Request"
                response = make_response(formatError(errorStr),400)
                return response
            else:
                return result
        else:
            query = { SENSOR_ID: sensorId,  "t":{"$gte" : startTimeInt}, "freqRange":populate_db.freqRange(minfreq,maxfreq)}
            debugPrint(query)
            msg = db.dataMessages.find_one(query)
            if msg == None:
                errorStr = "Data message not found for " + startTime
                debugPrint(errorStr)
                return make_response(formatError(errorStr),404)
            return generateSingleDaySpectrogramAndOccupancyForSweptFrequency(msg,sessionId,startTimeInt,minfreq,maxfreq)
    except:
         print "Unexpected error:", sys.exc_info()[0]
         print sys.exc_info()
         raise


@app.route("/spectrumbrowser/generateSpectrum/<sensorId>/<start>/<timeOffset>/<sessionId>", methods=["POST"])
def generateSpectrum(sensorId,start,timeOffset,sessionId):
    if not checkSessionId(sessionId):
        abort(404)
    startTime = int(start)
    # get the type of the measurement.
    msg = db.dataMessages.find_one({SENSOR_ID:sensorId})
    if msg["mType"] == "FFT-Power":
        msg = db.dataMessages.find_one({SENSOR_ID:sensorId,"t":startTime})
        if msg == None:
            errorStr = "dataMessage not found " + dataMessageOid
            debugPrint(errorStr)
            abort(404)
        milisecOffset = int(timeOffset)
        return generateSpectrumForFFTPower(msg,milisecOffset,sessionId)
    else :
        secondOffset = int(timeOffset)
        time = secondOffset+startTime
        print "time " , time
        time = secondOffset+startTime
        msg = db.dataMessages.find_one({SENSOR_ID:sensorId,"t":{"$gte": time}})
        if msg == None:
            errorStr = "dataMessage not found "
            debugPrint(errorStr)
            abort(404)
        return generateSpectrumForSweptFrequency(msg,sessionId)


@app.route("/spectrumbrowser/generatePowerVsTime/<sensorId>/<startTime>/<freq>/<sessionId>", methods=["POST"])
def generatePowerVsTime(sensorId,startTime,freq,sessionId):
    if not checkSessionId(sessionId):
        abort(404)
    msg = db.dataMessages.find_one({SENSOR_ID:sensorId})
    if msg == None:
        debugPrint("Message not found")
        abort(404)
    if msg["mType"] == "FFT-Power":
        msg = db.dataMessages.find_one({SENSOR_ID:sensorId,"t":int(startTime)})
        if msg == None:
            errorMessage = "Message not found"
            debugPrint(errorMessage)
            abort(404)
        freqHz = int(freq)
        return generatePowerVsTimeForFFTPower(msg,freqHz,sessionId)
    else:
        msg = db.dataMessages.find_one({SENSOR_ID:sensorId, "t": {"$gt":int(startTime)}})
        if msg == None:
            errorMessage = "Message not found"
            debugPrint(errorMessage)
            abort(404)
        freqHz = int(freq)
        return generatePowerVsTimeForSweptFrequency(msg,freqHz,sessionId)

@app.route("/spectrumdb/upload", methods=["POST"])
def upload() :
    msg =  request.data
    populate_db.put_message(msg)
    return "OK"


@sockets.route("/sensordata",methods=["POST","GET"])
def getSensorData(ws):
    """
    Handle sensor data streaming requests.
    """
    try :
        print "getSensorData"
        token = ws.receive()
        print "token = " ,token
        parts = token.split(":")
        sessionId = parts[0]
        if not checkSessionId(sessionId):
            ws.close()
            return
        sensorId = parts[1]
        debugPrint("sensorId " + sensorId)
        if not sensorId in lastDataMessage :
            ws.send(dumps({"status":"NO_DATA"}))
        else:
            ws.send(dumps({"status":"OK"}))
            ws.send(lastDataMessage[sensorId])
            lastdatatime =  -1
            while True:
                if lastdatatime != lastdataseen[sensorId]:
                    lastdatatime = lastdataseen[sensorId]
                    ws.send(sensordata[sensorId])
                gevent.sleep(SECONDS_PER_FRAME)
    except:
        ws.close()
        print "Error writing to websocket"


@sockets.route("/spectrumdb/stream",methods=["POST"])
def datastream(ws):
    print "Got a connection"
    bbuf = MyByteBuffer(ws)
    count = 0
    while True:
        lengthString = ""
        while True:
            lastChar = bbuf.readChar()
            if len(lengthString) > 1000:
                raise Exception("Formatting error")
            if lastChar == '{':
                print lengthString
                headerLength = int(lengthString.rstrip())
                break
            else:
                lengthString += str(lastChar)
        jsonStringBytes = "{"
        while len(jsonStringBytes) < headerLength:
            jsonStringBytes += str(bbuf.readChar())

        jsonData = json.loads(jsonStringBytes)
        print dumps(jsonData,sort_keys=True,indent=4)
        if jsonData["Type"] == "Data":
            dataSize  = jsonData["nM"]*jsonData["mPar"]["n"]
            td = jsonData["mPar"]["td"]
            nM = jsonData["nM"]
            n = jsonData["mPar"]["n"]
            sensorId = jsonData["SensorID"]
            lastDataMessage[sensorId] = jsonStringBytes
            timePerMeasurement = float(td)/float(nM)
            spectrumsPerFrame = int(SECONDS_PER_FRAME/timePerMeasurement)
            measurementsPerFrame = spectrumsPerFrame*n
            debugPrint("measurementsPerFrame : " + str(measurementsPerFrame) + " n = " + str(n) + " spectrumsPerFrame = " + str(spectrumsPerFrame))
            cutoff = jsonData["wnI"] + 2
            while True:
                counter = 0
                startTime = time.time()
                if peakDetection:
                    powerVal = [-100 for i in range(0,n)]
                else:
                    powerVal = [0 for i in range(0,n)]
                for i in range(0,measurementsPerFrame):
                    data = bbuf.readByte()
                    if peakDetection:
                        powerVal[i%n] = np.maximum(powerVal[i%n],data)
                    else:
                        powerVal[i%n] += data
                if not peakDetection:
                    for i in range(0,len(powerVal)):
                        powerVal[i] = powerVal[i]/spectrumsPerFrame
                # sending data as CSV values.
                sensordata[sensorId] = str(powerVal)[1:-1].replace(" ","")
                lastdataseen[sensorId] = time.time()
                endTime = time.time()
                delta = 0.7*SECONDS_PER_FRAME - endTime + startTime
                if delta > 0:
                    gevent.sleep(delta)
                else:
                    gevent.sleep(0.7*SECONDS_PER_FRAME)
                #print "count " , count
        elif jsonData["Type"] == "Sys":
            print "Got a System message"
        elif jsonData["Type"] == "Loc":
            print "Got a Location Message"

@sockets.route("/spectrumdb/test",methods=["POST"])
def websockettest(ws):
    count = 0
    try :
        msg = ws.receive()
        print "got something " + str(msg)
        while True:
            gevent.sleep(0.5)
            dataAscii = ws.receive()
            data = binascii.a2b_base64(dataAscii)
            count += len(data)
            print "got something " + str(count) + str(data)
    except:
        raise

@app.route("/spectrumbrowser/log", methods=["POST"])
def log():
    data = request.data
    jsonValue = json.loads(data)
    message = jsonValue["message"]
    print "Log Message : " + message
    exceptionInfo = jsonValue["ExceptionInfo"]
    if len(exceptionInfo) != 0 :
        print "Exception Info:"
        for i in range(0,len(exceptionInfo)):
            print "Exception Message:"
            exceptionMessage = exceptionInfo[i]["ExceptionMessage"]
            print "Stack Trace :"
            stackTrace = exceptionInfo[i]["StackTrace"]
            print exceptionMessage
            decodeStackTrace(stackTrace)
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
    launchedFromMain = True
    loadGwtSymbolMap()
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    #app.run('0.0.0.0',port=8000,debug="True")
    server = pywsgi.WSGIServer(('0.0.0.0', 8000), app, handler_class=WebSocketHandler)
    server.serve_forever()

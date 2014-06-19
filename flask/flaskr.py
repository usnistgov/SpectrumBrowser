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
import gridfs
import ast
import datetime
import pytz
import calendar
import timezone
import png
import populate_db



sessions = {}
secureSessions = {}
gwtSymbolMap = {}

app = Flask(__name__,static_url_path="")
random.seed(10)
client = MongoClient()
db = client.spectrumdb
debug = True
HOURS_PER_DAY = 24
MINUTES_PER_DAY = HOURS_PER_DAY*60
SECONDS_PER_DAY = MINUTES_PER_DAY*60
MILISECONDS_PER_DAY = SECONDS_PER_DAY*1000
UNDER_CUTOFF_COLOR='#D6D6DB'
OVER_CUTOFF_COLOR='#000000'
SENSOR_ID = "SensorID"

######################################################################################
# Internal functions (not exported as web services).
######################################################################################

# get the data associated with a message.
def getData(msg) :
    fs = gridfs.GridFS(db,msg[SENSOR_ID]+ "/data")
    messageBytes = fs.get(ObjectId(msg["dataKey"])).read()
    if msg["DataType"] == "ASCII":
        powerVal = eval(messageBytes)
    elif msg["DataType"] == "Binary - int8":
        powerVal = np.array(np.zeros(n*nM))
        for i in range(0,lengthToRead):
            powerVal[i] = float(struct.unpack('b',messageBytes[i:i+1])[0])
    elif msg["DataType"] == "Binary - int16":
        powerVal = np.array(np.zeros(n*nM))
        for i in range(0,lengthToRead):
            powerVal[i] = float(struct.unpack('h',messageBytes[i:i+2])[0])
    elif msg["DataType"] == "Binary - float32":
        powerVal = np.array(np.zeros(n*nM))
        for i in range(0,lengthToRead):
            powerVal[i] = float(struct.unpack('f',messageBytes[i:i+4])[0])
    return powerVal


def loadGwtSymbolMap():
    symbolMapDir = "static/WEB-INF/deploy/spectrumbrowser/symbolMaps/"
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

def getLocationMessage(msg):
    return db.locationMessages.find_one({SENSOR_ID:msg[SENSOR_ID], "t": {"$lte":msg["t"]}})

def getNextAcquisition(msg):
    query = {SENSOR_ID: msg[SENSOR_ID], "t":{"$gt": msg["t"]}}
    return db.dataMessages.find_one(query)

def getPrevAcquisition(msg):
    query = {SENSOR_ID: msg[SENSOR_ID], "t":{"$lt": msg["t"]}}
    cur =  db.dataMessages.find(query)
    if cur == None or cur.count() == 0:
        debugPrint("no message found")
        return None
    sortedCur = cur.sort('t',pymongo.DESCENDING).limit(10)
    return sortedCur.next()

def getPrevDayBoundary(msg):
    prevMsg = getPrevAcquisition(msg)
    if prevMsg == None:
        locationMessage = getLocationMessage(msg)
        return  timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg['t'],locationMessage['timeZone'])
    locationMessage = getLocationMessage(prevMsg)
    timeZone = locationMessage['timeZone']
    return timezone.getDayBoundaryTimeStampFromUtcTimeStamp(prevMsg['t'],timeZone)

def getNextDayBoundary(msg):
    nextMsg = getNextAcquisition(msg)
    if nextMsg == None:
        locationMessage = getLocationMessage(msg)
        return  timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg['t'],locationMessage['timeZone'])
    locationMessage = getLocationMessage(nextMsg)
    timeZone = locationMessage['timeZone']
    nextDayBoundary =  timezone.getDayBoundaryTimeStampFromUtcTimeStamp(nextMsg['t'],timeZone)
    if debug:
        thisDayBoundary =   timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg['t'],locationMessage['timeZone'])
        print "getNextDayBoundary: dayBoundary difference ", (nextDayBoundary - thisDayBoundary)/60/60
    return nextDayBoundary

# get minute index offset from given time in seconds.
# startTime is the starting time from which to compute the offset.
def getIndex(time,startTime) :
    return int ( float(time - startTime) / float(60) )


def generateOccupancyForFFTPower(msg,fileNamePrefix):
    measurementDuration = msg["mPar"]["td"]
    miliSecondsPerMeasurement = float(measurementDuration*1000)/float(nM)
    # Generate the occupancy stats for the acquisition.
    occupancyCount = [0 for i in range(0,nM)]
    for i in range(0,nM):
        occupancyCount[i] = float(len(filter(lambda x: x>=cutoff, spectrogramData[i,:])))/float(n)*100
    timeArray = [i*miliSecondsPerMeasurement for i in range(0,nM)]
    minOccupancy = np.minimum(occupancyCount)
    maxOccupancy = np.maximum(occupancyCount)
    plt.axes([0,measurementDuration*1000,minOccupancy,maxOccupancy])
    plt.xlim([0,measurementDuration*1000])
    plt.plot(timeArray,occupancyCount,"g.")
    plt.xlabel("Time (ms) since start of acquisition")
    plt.ylabel("Band Occupancy (%)")
    plt.title("Band Occupancy; Cutoff : " + str(cutoff))
    occupancyFilePath = "static/generated/" + fileNamePrefix + '.occupancy.png'
    plt.savefig(occupancyFilePath)
    plt.close('all')
    return  fileNamePrefix + ".occupancy.png"

def computeDailyMaxMinMeanMedianStats(cursor):
    meanOccupancy = 0
    minOccupancy = 10000
    maxOccupancy = -1
    occupancy = []
    powerArray = []
    n = 0
    nM = 0
    for msg in cursor:
        occupancy.append(msg['occupancy'])
        n = msg["mPar"]["n"]
        nM = msg["nM"]
        minFreq = msg["mPar"]["fStart"]
        maxFreq = msg["mPar"]["fStop"]
        cutoff = msg["cutoff"]
    maxOccupancy = float(np.max(occupancy))
    minOccupancy = float(np.min(occupancy))
    meanOccupancy = float(np.mean(occupancy))
    print maxOccupancy,minOccupancy,meanOccupancy
    medianOccupancy = float(np.median(occupancy))
    print medianOccupancy
    retval =  (n, maxFreq,minFreq,cutoff, \
        {"maxOccupancy":maxOccupancy, "minOccupancy":minOccupancy, "meanOccupancy":meanOccupancy, "medianOccupancy":medianOccupancy})
    debugPrint(retval)
    return retval

# Compute the daily max min and mean stats. The cursor starts on a day 
# boundary and ends on a day boundary.
def computeDailyMaxMinMeanStats(cursor):
    debugPrint("computeDailyMaxMinMeanStats")
    meanOccupancy = 0
    minOccupancy = 10000
    maxOccupancy = -1
    occupancy = []
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
        {"maxOccupancy":maxOccupancy, "minOccupancy":minOccupancy, "meanOccupancy":meanOccupancy})

def generateSingleDaySpectrogramAndOccupancyForSweptFrequency(msg,sessionId,startTime):
    locationMessage = getLocationMessage(msg)
    tz =  locationMessage['timeZone']
    startTimeUtc = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(startTime,tz)
    startMsg = db.dataMessages.find_one({SENSOR_ID:msg[SENSOR_ID],"t":{"$gte":startTimeUtc}})
    msg = startMsg


    noiseFloor = msg["wnI"]
    vectorLength = msg["mPar"]["n"]
    fstop = msg['mPar']['fStop']
    fstart = msg['mPar']['fStart']
    cutoff = int(request.args.get("cutoff",msg['cutoff']))
    powerVal = np.array([cutoff for i in range(0,MINUTES_PER_DAY*vectorLength)])
    spectrogramData = powerVal.reshape(vectorLength,MINUTES_PER_DAY)
    # artificial power value when sensor is off.
    sensorOffPower = np.transpose(np.array([2000 for i in range(0,vectorLength)]))
    prevStart = startTimeUtc
    sensorId = msg[SENSOR_ID]

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
        occupancy.append(msg['occupancy'])
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
    frame1 = plt.gca()
    frame1.axes.get_xaxis().set_visible(False)
    frame1.axes.get_yaxis().set_visible(False)
    cmap = plt.cm.spectral
    cmap.set_under(UNDER_CUTOFF_COLOR)
    cmap.set_over(OVER_CUTOFF_COLOR)
    dirname = "static/generated/" + sessionId
    if not os.path.exists(dirname):
        os.makedirs("static/generated/" + sessionId)
    fig = plt.imshow(spectrogramData,interpolation='none',origin='lower', aspect="auto",vmin=cutoff,vmax=maxpower,cmap=cmap)
    print "Generated fig"
    spectrogramFile =  sessionId + "/" +sensorId + "." + str(startTimeUtc) + "." + str(cutoff)
    spectrogramFilePath = "static/generated/" + spectrogramFile
    plt.savefig(spectrogramFilePath + '.png', bbox_inches='tight', pad_inches=0, dpi=100)
    plt.close('all')

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
            "timeZone" : tzName,                                    \
            "maxFreq":float(fstop),                                 \
            "minFreq":float(fstart),                                \
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

# Generate a spectrogram and occupancy plot for FFTPower data starting at msg.
def generateSingleAcquisitionSpectrogramAndOccupancyForFFTPower(msg,sessionId):
    startTime = msg['t']
    fs = gridfs.GridFS(db,msg[SENSOR_ID] + "/data")
    messageBytes = fs.get(ObjectId(msg["dataKey"])).read()
    debugPrint("Read " + str(len(messageBytes)))
    cutoff = int(request.args.get("cutoff",msg['cutoff']))
    noiseFloor = msg['wnI']
    nM = msg["nM"]
    n = msg["mPar"]["n"]
    measurementDuration = msg["mPar"]["td"]
    miliSecondsPerMeasurement = float(measurementDuration*1000)/float(nM)
    locationMessage = getLocationMessage(msg)
    lengthToRead = n*nM
    # Read the power values
    occupancyCount = 0
    powerVal = getData(msg)
    for i in range(0,lengthToRead):
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
    sensorId = msg[SENSOR_ID]
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
    nextAcquisition = getNextDataMessage(msg)
    prevAcquisition = getPrevDataMessage(msg)
    
    if nextAcquisiton != None:
        nextAcquisitionTime = nextAcquistion['t']
    else:
        nextAcquisitionTime = msg['t']

    if prevAcuisition != None:
        prevAcquisitionTime = prevAcquisiton['t']
    else:
        prevAcquisitionTime = msg['t']

    tz =  locationMessage['timeZone']

    result = {"spectrogram": spectrogramFile+".png",                \
            "cbar":spectrogramFile+".cbar.png",                     \
            "maxPower":maxpower,                                    \
            "cutoff":cutoff,                                        \
            "noiseFloor" : noiseFloor,                              \
            "minPower":minpower,                                    \
            "tStartLocalTime": localTime,                           \
            "timeZone" : tzName,                                    \
            "maxFreq":msg["mPar"]["fStop"],                         \
            "minFreq":msg["mPar"]["fStart"],                        \
            "timeDelta":msg["mPar"]["td"],                          \
            "prevAcquisition" : prevAcquisitionTime ,               \
            "nextAcquisition" : nextAcquisitionTime ,               \
            "formattedDate" : timezone.formatTimeStampLong(msg['t'], tz), \
            "image_width":float(width),                             \
            "image_height":float(height)}
    # see if it is well formed.
    print "Computed result"
    debugPrint(result)
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
    plt.scatter(freqArray,spectrumData)
    plt.xlabel("Freq (MHz)")
    plt.ylabel("Power (dBm)")
    locationMessage = db.locationMessages.find_one({"_id": ObjectId(msg["locationMessageId"])})
    t  = msg["t"]
    tz =  locationMessage['timeZone']
    plt.title("Spectrum at " + timezone.formatTimeStampLong(t,tz))
    spectrumFile =  sessionId + "/" +msg[SENSOR_ID] + "." + str(msg['t']) + ".spectrum.png"
    spectrumFilePath = "static/generated/" + spectrumFile
    plt.savefig(spectrumFilePath,  pad_inches=0, dpi=100)
    plt.close("all")
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
    lengthToRead = nM*n
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
    plt.scatter(freqArray,spectrumData)
    plt.xlabel("Freq (MHz)")
    plt.ylabel("Power (dBm)")
    locationMessage = db.locationMessages.find_one({"_id": ObjectId(msg["locationMessageId"])})
    t  = msg["t"] + milisecOffset/float(1000)
    tz =  locationMessage['timeZone']
    plt.title("Spectrum at " + timezone.formatTimeStampLong(t,tz))
    spectrumFile =  sessionId + "/" +msg[SENSOR_ID] + "." + str(startTime) + "." + str(milisecOffset) + ".spectrum.png"
    spectrumFilePath = "static/generated/" + spectrumFile
    plt.savefig(spectrumFilePath,  pad_inches=0, dpi=100)
    plt.close("all")
    retval = {"spectrum" : spectrumFile }
    debugPrint(retval)
    return jsonify(retval)

def generatePowerVsTimeForSweptFrequency(msg,freqMHz,sessionId):
    (maxFreq,minFreq) = getMaxMinFreq(msg)
    locationMessage = getLocationMessage(msg)
    timeZone = locationMessage['timeZone']
    freqHz = freqMHz*1E6
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

    plt.xlim([0,23])
    plt.title("Power vs. Time at "+ str(freqMHz) + " MHz")
    plt.xlabel("Time from start of day (Hours)")
    plt.ylabel("Power (dBm)")
    plt.xlim([0,23])
    plt.scatter(timeArray,powerArray)
    spectrumFile =  sessionId + "/" +msg[SENSOR_ID] + "." + str(startTime) + "." + str(freqMHz) + ".power.png"
    spectrumFilePath = "static/generated/" + spectrumFile
    plt.savefig(spectrumFilePath,  pad_inches=0, dpi=100)
    plt.close("all")
    retval = {"powervstime" : spectrumFile }
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
    powerVal = getData(msg)
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
    timeArray = [i*miliSecondsPerMeasurement for i in range(0,nM)]
    plt.xlim([0,measurementDuration*1000])
    plt.scatter(timeArray,powerValues)
    plt.title("Power vs. Time at "+ str(freqMHz) + " MHz")
    spectrumFile =  sessionId + "/" +msg[SENSOR_ID] + "." + str(startTime) + "." + str(freqMHz) + ".power.png"
    spectrumFilePath = "static/generated/" + spectrumFile
    plt.xlabel("Time from start of acquistion (ms)")
    plt.ylabel("Power (dBm)")
    plt.savefig(spectrumFilePath,  pad_inches=0, dpi=100)
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
        (c["tStartLocalTime"],c["tStartLocalTimeTzName"]) = timezone.getLocalTime(c["t"],c["timeZone"])
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
    queryString = { SENSOR_ID : sensorId, "t" : {'$gte':tstart,'$lte': tstart + SECONDS_PER_DAY}}
    startMessage =  db.dataMessages.find_one(queryString)
    locationMessage = getLocationMessage(startMessage)
    tZId = locationMessage["timeZone"]
    if locationMessage == None:
        return jsonify(None),404
    tmin = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(startMessage['t'],tZId)
    result = {}
    values = {}
    for day in range(0,ndays):
        tstart = tmin +  day*SECONDS_PER_DAY
        tend = tstart + SECONDS_PER_DAY
        queryString = { SENSOR_ID : sensorId, "t" : {'$gte':tstart,'$lte': tend}}
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
    result["maxFreq"] = maxFreq/1E6
    result["minFreq"] = minFreq/1E6
    result["cutoff"] = cutoff
    result["channelCount"] = nChannels
    result["startDate"] = timezone.formatTimeStampLong(tmin,tZId)
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
    dayCount = request.args.get('dayCount','')
    tzId = locationMessage["timeZone"]
    if tmin == '' and dayCount == '':
        query = { SENSOR_ID: sensorId, "locationMessageId":locationMessageId }
    elif tmin != ''  and dayCount == '' :
        mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin),tzId)
        query = { SENSOR_ID:sensorId, "locationMessageId":locationMessageId, "t" : {'$gte':mintime} }
    else:
        mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin),tzId)
        maxtime = mintime + int(dayCount)*SECONDS_PER_DAY
        query = { SENSOR_ID: sensorId, "locationMessageId":locationMessageId, "t": { '$lte':maxtime, '$gte':mintime}  }
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
            tStartDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg["t"],tzId)
            tz =  locationMessage['timeZone']
            (minLocalTime,tStartLocalTimeTzName) = timezone.getLocalTime(msg['t'],tz)
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
    tz =  locationMessage['timeZone']
    (tEndReadingsLocalTime,tEndReadingsLocalTimeTzName) = timezone.getLocalTime(lastMessage['t'],tz)
    tEndDayBoundary = endDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(lastMessage["t"],tz)
    meanOccupancy = meanOccupancy/nreadings
    retval = {"minOccupancy":minOccupancy,                    \
        "tStartReadings":minTime,                                   \
        "tStartLocalTime": minLocalTime,                            \
        "tStartLocalTimeTzName" : tStartLocalTimeTzName,            \
        "tStartLocalTimeFormattedTimeStamp" : timezone.formatTimeStampLong(minTime,tz), \
        "tStartDayBoundary":float(tStartDayBoundary),               \
        "tEndReadings":float(maxTime),                              \
        "tEndReadingsLocalTime":float(tEndReadingsLocalTime),       \
        "tEndReadingsLocalTimeTzName" : tEndReadingsLocalTimeTzName, \
        "tEndLocalTimeFormattedTimeStamp" : timezone.formatTimeStampLong(maxTime,tz), \
        "tEndDayBoundary":float(tEndDayBoundary),                   \
        "maxOccupancy":maxOccupancy,                                \
        "meanOccupancy":meanOccupancy,                              \
        "maxFreq":maxFreq,                                          \
        "minFreq":minFreq,                                          \
        "measurementType": measurementType,                         \
        "readingsCount":float(nreadings)}
    print retval
    return jsonify(retval)



@app.route("/spectrumbrowser/getOneDayStats/<sensorId>/<startTime>/<sessionId>", methods=["POST"])
def getOneDayStats(sensorId,startTime,sessionId):
    """
    Get the statistics for a given sensor given a start time for a single day of data.
    The time is rounded to the start of the day boundary.
    """
    mintime = int(startTime)
    maxtime = mintime + SECONDS_PER_DAY
    query = { SENSOR_ID: sensorId,  "t": { '$lte':maxtime, '$gte':mintime}  }
    debugPrint(query)
    msg =  db.dataMessages.find_one(query)
    query = { "_id": ObjectId(msg["locationMessageId"]) }
    locationMessage = db.locationMessages.find_one(query)
    mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg["t"],locationMessage["timeZone"])
    maxtime = mintime + SECONDS_PER_DAY
    query = { SENSOR_ID: sensorId,  "t": { '$lte':maxtime, '$gte':mintime}  }
    cur = db.dataMessages.find(query)
    if cur == None:
        abort(404)
    res = {}
    values = {}
    res["formattedDate"] = timezone.formatTimeStampLong(mintime,locationMessage["timeZone"])
    for msg in cur:
        maxFreq = msg["mPar"]["fStop"]
        minFreq = msg["mPar"]["fStart"]
        channelCount = msg["mPar"]["n"]
        cutoff = msg["cutoff"]
        values[(msg["t"]-mintime)] = {"t": msg["t"], \
                        "maxPower" : msg["maxPower"],\
                        "minPower" : msg["minPower"],\
                        "maxOccupancy":msg["maxOccupancy"],\
                        "minOccupancy":msg["minOccupancy"],\
                        "meanOccupancy":msg["meanOccupancy"],\
                        "medianOccupancy":msg["medianOccupancy"]}
    res["maxFreq"] = maxFreq/1E6
    res["minFreq"] = minFreq/1E6
    res["channelCount"] = channelCount
    res["cutoff"] = cutoff
    res["values"] = values
    return jsonify(res)


@app.route("/spectrumbrowser/generateSingleAcquisitionSpectrogramAndOccupancy/<sensorId>/<startTime>/<sessionId>", methods=["POST"])
def generateSingleAcquisitionSpectrogram(sensorId,startTime,sessionId):
    """ Generate the single acquisiton spectrogram or the daily spectrogram.
        sensorId is the sensor ID of interest.
        The start time is a day boundary timeStamp for swept freq.
        The start time is the time stamp for the data message for FFT power. """
    if not checkSessionId(sessionId):
        abort(404)
    startTimeInt = int(startTime)
    query = { SENSOR_ID: sensorId}
    msg = db.dataMessages.find_one(query)
    if msg == None:
        debugPrint("Sensor ID not found " + sensorId)
        return {"ErrorMessage":"Sensor ID not found " + sensorId},404
    if msg["mType"] == "FFT-Power":
        query = { SENSOR_ID: sensorId,  "t": startTimeInt}
        debugPrint(query)
        msg = db.dataMessages.find_one(query)
        if msg == None:
            errorStr = "Data message not found for " + startTime
            return {"ErrorMessage":errorStr}, 404
        return generateSingleAcquisitionSpectrogramAndOccupancyForFFTPower(msg,sessionId)
    else:
        query = { SENSOR_ID: sensorId,  "t":{"$gte" : startTimeInt}}
        debugPrint(query)
        msg = db.dataMessages.find_one(query)
        if msg == None:
            errorStr = "Data message not found for " + startTime
            return {"ErrorMessage":errorStr}, 404
        return generateSingleDaySpectrogramAndOccupancyForSweptFrequency(msg,sessionId,startTimeInt)


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
            return {"ErrorMessage":errorStr}, 404
        milisecOffset = int(timeOffset)
        return generateSpectrumForFFTPower(msg,milisecOffset,sessionId)
    else :
        secondOffset = int(timeOffset)
        time = secondOffset+startTime
        print "time " , time
        time = secondOffset+startTime
        msg = db.dataMessages.find_one({SENSOR_ID:sensorId,"t":{"$gte": time}})
        if msg == None:
            errorStr = "dataMessage not found " + dataMessageOid
            return {"ErrorMessage":errorStr}, 404
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
            return {"ErrorMessage":errorMessage},404
        freqMHz = int(freq)
        return generatePowerVsTimeForFFTPower(msg,freqMHz,sessionId)
    else:
        msg = db.dataMessages.find_one({SENSOR_ID:sensorId, "t": {"$gt":int(startTime)}})
        if msg == None:
            errorMessage = "Message not found"
            return {"ErrorMessage":errorMessage},404
        freqMHz = int(freq)
        return generatePowerVsTimeForSweptFrequency(msg,freqMHz,sessionId)

@app.route("/spectrumdb/upload", methods=["POST"])
def upload() :
    msg =  request.data
    populate_db.put_message(msg)
    return "OK"

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
    #app.run('0.0.0.0',debug="True",port=8443,ssl_context='adhoc')
    loadGwtSymbolMap()
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.run('localhost',debug="True")

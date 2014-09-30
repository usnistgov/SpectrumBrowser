from flask import Flask, request, abort, make_response
from flask import jsonify
import random
import struct
import json
import pymongo
import numpy as np
import os
from pymongo import MongoClient
from bson.json_util import dumps
from bson.objectid import ObjectId
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import time
import urlparse
import gridfs
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
import traceback
import GenerateZipFileForDownload
import GetLocationInfo
import GetDailyMaxMinMeanStats
import util
import msgutils
import authentication
import GeneratePowerVsTime




sessions = {}
secureSessions = {}
gwtSymbolMap = {}

# move these to another module
sensordata = {}
lastDataMessage = {}
lastdataseen = {}

peakDetection = True
launchedFromMain = False
app = Flask(__name__, static_url_path="")
sockets = Sockets(app)
random.seed(10)
mongodb_host = os.environ.get('DB_PORT_27017_TCP_ADDR', 'localhost')
client = MongoClient(mongodb_host)
db = client.spectrumdb
debug = True
HOURS_PER_DAY = 24
MINUTES_PER_DAY = HOURS_PER_DAY * 60
SECONDS_PER_DAY = MINUTES_PER_DAY * 60
MILISECONDS_PER_DAY = SECONDS_PER_DAY * 1000
UNDER_CUTOFF_COLOR = '#D6D6DB'
OVER_CUTOFF_COLOR = '#000000'
SENSOR_ID = "SensorID"
TIME_ZONE_KEY = "timeZone"
SECONDS_PER_FRAME = 0.1


flaskRoot = os.environ['SPECTRUM_BROWSER_HOME'] + "/flask/"



######################################################################################
# Internal functions (not exported as web services).
######################################################################################



class MyByteBuffer:

    def __init__(self, ws):
        self.ws = ws
        self.queue = Queue()
        self.buf = BytesIO()


    def readFromWebSocket(self):
        dataAscii = self.ws.receive()
        if dataAscii != None:
            data = binascii.a2b_base64(dataAscii)
            # print data
            if data != None:
                bio = BytesIO(data)
                bio.seek(0)
                self.queue.put(bio)
        return

    def read(self, size):
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
        retval = struct.unpack(">b", val)[0]
        return retval

    def readChar(self):
        val = self.read(1)
        return val

    def size(self):
        return self.size


def checkSessionId(sessionId):
    if debug :
        return True
    elif sessions[request.remote_addr] == None :
        return False
    elif sessions[request.remote_addr] != sessionId :
        return False
    return True


# get minute index offset from given time in seconds.
# startTime is the starting time from which to compute the offset.
def getIndex(time, startTime) :
    return int (float(time - startTime) / float(60))


def generateOccupancyForFFTPower(msg, fileNamePrefix):
    measurementDuration = msg["mPar"]["td"]
    nM = msg['nM']
    n = msg['mPar']['n']
    cutoff = msg['cutoff']
    miliSecondsPerMeasurement = float(measurementDuration * 1000) / float(nM)
    spectrogramData = msgutils.getData(msg)
    # Generate the occupancy stats for the acquisition.
    occupancyCount = [0 for i in range(0, nM)]
    for i in range(0, nM):
        occupancyCount[i] = util.roundTo3DecimalPlaces(float(len(filter(lambda x: x >= cutoff, spectrogramData[i, :]))) / float(n) * 100)
    timeArray = [i * miliSecondsPerMeasurement for i in range(0, nM)]
    minOccupancy = np.minimum(occupancyCount)
    maxOccupancy = np.maximum(occupancyCount)
    plt.figure(figsize=(6, 4))
    plt.axes([0, measurementDuration * 1000, minOccupancy, maxOccupancy])
    plt.xlim([0, measurementDuration * 1000])
    plt.plot(timeArray, occupancyCount, "g.")
    plt.xlabel("Time (ms) since start of acquisition")
    plt.ylabel("Band Occupancy (%)")
    plt.title("Band Occupancy; Cutoff : " + str(cutoff))
    occupancyFilePath = util.getPath("static/generated/") + fileNamePrefix + '.occupancy.png'
    plt.savefig(occupancyFilePath)
    plt.clf()
    plt.close()
    # plt.close('all')
    return  fileNamePrefix + ".occupancy.png"

def trimSpectrumToSubBand(msg, subBandMinFreq, subBandMaxFreq):
    data = msgutils.getData(msg)
    n = msg["mPar"]["n"]
    minFreq = msg["mPar"]["fStart"]
    maxFreq = msg["mPar"]["fStop"]
    freqRangePerReading = float(maxFreq - minFreq) / float(n)
    endReadingsToIgnore = int((maxFreq - subBandMaxFreq) / freqRangePerReading)
    topReadingsToIgnore = int((subBandMinFreq - minFreq) / freqRangePerReading)
    powerArray = np.array([data[i] for i in range(topReadingsToIgnore, n - endReadingsToIgnore)])
    # util.debugPrint("Length " + str(len(powerArray)))
    return powerArray



def generateSingleDaySpectrogramAndOccupancyForSweptFrequency(msg, sessionId, startTime, fstart, fstop, subBandMinFreq, subBandMaxFreq):
    try :
        locationMessage = msgutils.getLocationMessage(msg)
        tz = locationMessage[TIME_ZONE_KEY]
        startTimeUtc = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(startTime, tz)
        startMsg = db.dataMessages.find_one({SENSOR_ID:msg[SENSOR_ID], "t":{"$gte":startTimeUtc}, \
                "freqRange":populate_db.freqRange(fstart, fstop)})
        if startMsg == None:
            util.debugPrint("Not found")
            abort(404)
        if startMsg['t'] - startTimeUtc > SECONDS_PER_DAY:
            util.debugPrint("Not found - outside day boundary")
            abort(404)

        msg = startMsg
        sensorId = msg[SENSOR_ID]
        noiseFloor = msg["wnI"]
        powerValues = trimSpectrumToSubBand(msg, subBandMinFreq, subBandMaxFreq)
        vectorLength = len(powerValues)
        cutoff = int(request.args.get("cutoff", msg['cutoff']))
        spectrogramFile = sessionId + "/" + sensorId + "." + str(startTimeUtc) + "." + str(cutoff) + "." + str(subBandMinFreq) + "." + str(subBandMaxFreq)
        spectrogramFilePath = util.getPath("static/generated/") + spectrogramFile
        powerVal = np.array([cutoff for i in range(0, MINUTES_PER_DAY * vectorLength)])
        spectrogramData = powerVal.reshape(vectorLength, MINUTES_PER_DAY)
        # artificial power value when sensor is off.
        sensorOffPower = np.transpose(np.array([2000 for i in range(0, vectorLength)]))

        prevMessage = msgutils.getPrevAcquisition(msg)

        if prevMessage == None:
            util.debugPrint ("prevMessage not found")
            prevMessage = msg
            prevAcquisition = sensorOffPower
        else:
            prevAcquisitionTime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(prevMessage['t'], tz)
            util.debugPrint ("prevMessage[t] " + str(prevMessage['t']) + " msg[t] " + str(msg['t']) + " prevDayBoundary " + str(prevAcquisitionTime))
            prevAcquisition = np.transpose(np.array(trimSpectrumToSubBand(prevMessage, subBandMinFreq, subBandMaxFreq)))
        occupancy = []
        timeArray = []
        maxpower = -1000
        minpower = 1000
        while True:
            acquisition = trimSpectrumToSubBand(msg, subBandMinFreq, subBandMaxFreq)
            minpower = np.minimum(minpower, msg['minPower'])
            maxpower = np.maximum(maxpower, msg['maxPower'])
            if prevMessage['t1'] != msg['t1']:
                 # GAP detected so fill it with sensorOff
                print "Gap generated"
                for i in range(getIndex(prevMessage["t"], startTimeUtc), getIndex(msg["t"], startTimeUtc)):
                    spectrogramData[:, i] = sensorOffPower
            elif prevMessage["t"] > startTimeUtc:
                # Prev message is the same tstart and prevMessage is in the range of interest.
                # Sensor was not turned off.
                # fill forward using the prev acquisition.
                for i in range(getIndex(prevMessage['t'], startTimeUtc), getIndex(msg["t"], startTimeUtc)):
                    spectrogramData[:, i] = prevAcquisition
            else :
                # forward fill from prev acquisition to the start time
                # with the previous power value
                for i in range(0, getIndex(msg["t"], startTimeUtc)):
                    spectrogramData[:, i] = prevAcquisition
            colIndex = getIndex(msg['t'], startTimeUtc)
            spectrogramData[:, colIndex] = acquisition
            timeArray.append(float(msg['t'] - startTimeUtc) / float(3600))
            occupancy.append(util.roundTo1DecimalPlaces(msg['occupancy']))
            prevMessage = msg
            prevAcquisition = acquisition
            msg = msgutils.getNextAcquisition(msg)
            if msg == None:
                lastMessage = prevMessage
                for i in range(getIndex(prevMessage["t"], startTimeUtc), MINUTES_PER_DAY):
                    spectrogramData[:, i] = sensorOffPower
                break
            elif msg['t'] - startTimeUtc > SECONDS_PER_DAY:
                for i in range(getIndex(prevMessage["t"], startTimeUtc), MINUTES_PER_DAY):
                    spectrogramData[:, i] = prevAcquisition
                lastMessage = prevMessage
                break

        # generate the spectrogram as an image.
        if not os.path.exists(spectrogramFilePath + ".png"):
           fig = plt.figure(figsize=(6, 4))
           frame1 = plt.gca()
           frame1.axes.get_xaxis().set_visible(False)
           frame1.axes.get_yaxis().set_visible(False)
           cmap = plt.cm.spectral
           cmap.set_under(UNDER_CUTOFF_COLOR)
           cmap.set_over(OVER_CUTOFF_COLOR)
           dirname = util.getPath("static/generated/") + sessionId
           if not os.path.exists(dirname):
              os.makedirs(dirname)
           fig = plt.imshow(spectrogramData, interpolation='none', origin='lower', aspect='auto', vmin=cutoff, vmax=maxpower, cmap=cmap)
           print "Generated fig"
           plt.savefig(spectrogramFilePath + '.png', bbox_inches='tight', pad_inches=0, dpi=100)
           plt.clf()
           plt.close()
        else:
           util.debugPrint("File exists - not generating image")

        util.debugPrint("FileName : " + spectrogramFilePath + ".png")

        util.debugPrint("Reading " + spectrogramFilePath + ".png")
        # get the size of the generated png.
        reader = png.Reader(filename=spectrogramFilePath + ".png")
        (width, height, pixels, metadata) = reader.read()

        util.debugPrint("width = " + str(width) + " height = " + str(height))

        # generate the colorbar as a separate image.
        if not os.path.exists(spectrogramFilePath + ".cbar.png") :
          norm = mpl.colors.Normalize(vmin=cutoff, vmax=maxpower)
          fig = plt.figure(figsize=(4, 10))
          ax1 = fig.add_axes([0.0, 0, 0.1, 1])
          mpl.colorbar.ColorbarBase(ax1, cmap=cmap, norm=norm, orientation='vertical')
          plt.savefig(spectrogramFilePath + '.cbar.png', bbox_inches='tight', pad_inches=0, dpi=50)
          plt.clf()
          plt.close()
        else:
          util.debugPrint(spectrogramFilePath + ".cbar.png" + " exists -- not generating")


        localTime, tzName = timezone.getLocalTime(startTimeUtc, tz)

        # step back for 24 hours.
        prevAcquisitionTime = msgutils.getPrevDayBoundary(startMsg)
        nextAcquisitionTime = msgutils.getNextDayBoundary(lastMessage)


        result = {"spectrogram": spectrogramFile + ".png", \
            "cbar":spectrogramFile + ".cbar.png", \
            "maxPower":maxpower, \
            "cutoff":cutoff, \
            "noiseFloor" : noiseFloor, \
            "minPower":minpower, \
            "tStartTimeUtc": startTimeUtc, \
            "timeDelta":HOURS_PER_DAY, \
            "prevAcquisition" : prevAcquisitionTime , \
            "nextAcquisition" : nextAcquisitionTime , \
            "formattedDate" : timezone.formatTimeStampLong(startTimeUtc, tz), \
            "image_width":float(width), \
            "image_height":float(height)}

        util.debugPrint(result)
        result["timeArray"] = timeArray
        result["occupancyArray"] = occupancy
        return jsonify(result)
    except  :
         print "Unexpected error:", sys.exc_info()[0]
         raise

# Generate a spectrogram and occupancy plot for FFTPower data starting at msg.
def generateSingleAcquisitionSpectrogramAndOccupancyForFFTPower(msg, sessionId):
    startTime = msg['t']
    fs = gridfs.GridFS(db, msg[SENSOR_ID] + "/data")
    sensorId = msg[SENSOR_ID]
    messageBytes = fs.get(ObjectId(msg["dataKey"])).read()
    util.debugPrint("Read " + str(len(messageBytes)))
    cutoff = int(request.args.get("cutoff", msg['cutoff']))
    leftBound = float(request.args.get("leftBound", 0))
    rightBound = float(request.args.get("rightBound", 0))
    spectrogramFile = sessionId + "/" + sensorId + "." + str(startTime) + "." + str(leftBound) + "." + str(rightBound) + "." + str(cutoff)
    spectrogramFilePath = util.getPath("static/generated/") + spectrogramFile
    if leftBound < 0 or rightBound < 0 :
        util.debugPrint("Bounds to exlude must be >= 0")
        return None
    measurementDuration = msg["mPar"]["td"]
    miliSecondsPerMeasurement = float(measurementDuration * 1000) / float(msg['nM'])
    leftColumnsToExclude = int(leftBound / miliSecondsPerMeasurement)
    rightColumnsToExclude = int(rightBound / miliSecondsPerMeasurement)
    if leftColumnsToExclude + rightColumnsToExclude >= msg['nM']:
        util.debugPrint("leftColumnToExclude " + str(leftColumnsToExclude) + " rightColumnsToExclude " + str(rightColumnsToExclude))
        return None
    util.debugPrint("LeftColumns to exclude " + str(leftColumnsToExclude) + " right columns to exclude " + str(rightColumnsToExclude))
    noiseFloor = msg['wnI']
    nM = msg["nM"] - leftColumnsToExclude - rightColumnsToExclude
    n = msg["mPar"]["n"]
    locationMessage = msgutils.getLocationMessage(msg)
    lengthToRead = n * msg["nM"]
    # Read the power values
    power = msgutils.getData(msg)
    powerVal = power[n * leftColumnsToExclude:lengthToRead - n * rightColumnsToExclude]
    minTime = float(leftColumnsToExclude * miliSecondsPerMeasurement) / float(1000)
    spectrogramData = powerVal.reshape(nM, n)
    # generate the spectrogram as an image.
    if not os.path.exists(spectrogramFilePath + ".png"):
       dirname = util.getPath("static/generated/") + sessionId
       if not os.path.exists(dirname):
           os.makedirs(util.getPath("static/generated/") + sessionId)
       fig = plt.figure(figsize=(6, 4))
       frame1 = plt.gca()
       frame1.axes.get_xaxis().set_visible(False)
       frame1.axes.get_yaxis().set_visible(False)
       maxpower = msg['maxPower']
       cmap = plt.cm.spectral
       cmap.set_under(UNDER_CUTOFF_COLOR)
       fig = plt.imshow(np.transpose(spectrogramData), interpolation='none', origin='lower', aspect="auto", vmin=cutoff, vmax=maxpower, cmap=cmap)
       print "Generated fig"
       plt.savefig(spectrogramFilePath + '.png', bbox_inches='tight', pad_inches=0, dpi=100)
       plt.clf()
       plt.close()
    else :
       util.debugPrint("File exists -- not regenerating")

    # generate the occupancy data for the measurement.
    occupancyCount = [0 for i in range(0, nM)]
    for i in range(0, nM):
        occupancyCount[i] = util.roundTo1DecimalPlaces(float(len(filter(lambda x: x >= cutoff, spectrogramData[i, :]))) / float(n) * 100)
    timeArray = [int((i + leftColumnsToExclude) * miliSecondsPerMeasurement)  for i in range(0, nM)]

    # get the size of the generated png.
    reader = png.Reader(filename=spectrogramFilePath + ".png")
    (width, height, pixels, metadata) = reader.read()

    if not os.path.exists(spectrogramFilePath + ".cbar.png"):
       # generate the colorbar as a separate image.
       norm = mpl.colors.Normalize(vmin=cutoff, vmax=maxpower)
       fig = plt.figure(figsize=(4, 10))
       ax1 = fig.add_axes([0.0, 0, 0.1, 1])
       mpl.colorbar.ColorbarBase(ax1, cmap=cmap, norm=norm, orientation='vertical')
       plt.savefig(spectrogramFilePath + '.cbar.png', bbox_inches='tight', pad_inches=0, dpi=50)
       plt.clf()
       plt.close()

    nextAcquisition = msgutils.getNextAcquisition(msg)
    prevAcquisition = msgutils.getPrevAcquisition(msg)

    if nextAcquisition != None:
        nextAcquisitionTime = nextAcquisition['t']
    else:
        nextAcquisitionTime = msg['t']

    if prevAcquisition != None:
        prevAcquisitionTime = prevAcquisition['t']
    else:
        prevAcquisitionTime = msg['t']

    tz = locationMessage[TIME_ZONE_KEY]

    timeDelta = msg["mPar"]["td"] - float(leftBound) / float(1000) - float(rightBound) / float(1000)

    result = {"spectrogram": spectrogramFile + ".png", \
            "cbar":spectrogramFile + ".cbar.png", \
            "maxPower":msg['maxPower'], \
            "cutoff":cutoff, \
            "noiseFloor" : noiseFloor, \
            "minPower":msg['minPower'], \
            "maxFreq":msg["mPar"]["fStop"], \
            "minFreq":msg["mPar"]["fStart"], \
            "minTime": minTime, \
            "timeDelta": timeDelta, \
            "prevAcquisition" : prevAcquisitionTime , \
            "nextAcquisition" : nextAcquisitionTime , \
            "formattedDate" : timezone.formatTimeStampLong(msg['t'] + leftBound , tz), \
            "image_width":float(width), \
            "image_height":float(height)}
    # see if it is well formed.
    print dumps(result, indent=4)
    # Now put in the occupancy data
    result["timeArray"] = timeArray
    result["occupancyArray"] = occupancyCount
    return jsonify(result)

def generateSpectrumForSweptFrequency(msg, sessionId, minFreq, maxFreq):
    try:
        spectrumData = trimSpectrumToSubBand(msg, minFreq, maxFreq)
        nSteps = len(spectrumData)
        freqDelta = float(maxFreq - minFreq) / float(1E6) / nSteps
        freqArray = [ float(minFreq) / float(1E6) + i * freqDelta for i in range(0, nSteps)]
        plt.figure(figsize=(6, 4))
        plt.scatter(freqArray, spectrumData)
        plt.xlabel("Freq (MHz)")
        plt.ylabel("Power (dBm)")
        locationMessage = db.locationMessages.find_one({"_id": ObjectId(msg["locationMessageId"])})
        t = msg["t"]
        tz = locationMessage[TIME_ZONE_KEY]
        plt.title("Spectrum at " + timezone.formatTimeStampLong(t, tz))
        spectrumFile = sessionId + "/" + msg[SENSOR_ID] + "." + str(msg['t']) + "." + str(minFreq) + "." + str(maxFreq) + ".spectrum.png"
        spectrumFilePath = util.getPath("static/generated/") + spectrumFile
        plt.savefig(spectrumFilePath, pad_inches=0, dpi=100)
        plt.clf()
        plt.close()
        # plt.close("all")
        retval = {"spectrum" : spectrumFile }
        util.debugPrint(retval)
        return jsonify(retval)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise


# generate the spectrum for a FFT power acquisition at a given milisecond offset.
# from the start time.
def generateSpectrumForFFTPower(msg, milisecOffset, sessionId):
    startTime = msg["t"]
    nM = msg["nM"]
    n = msg["mPar"]["n"]
    measurementDuration = msg["mPar"]["td"]
    miliSecondsPerMeasurement = float(measurementDuration * 1000) / float(nM)
    powerVal = msgutils.getData(msg)
    spectrogramData = np.transpose(powerVal.reshape(nM, n))
    col = milisecOffset / miliSecondsPerMeasurement
    util.debugPrint("Col = " + str(col))
    spectrumData = spectrogramData[:, col]
    maxFreq = msg["mPar"]["fStop"]
    minFreq = msg["mPar"]["fStart"]
    nSteps = len(spectrumData)
    freqDelta = float(maxFreq - minFreq) / float(1E6) / nSteps
    freqArray = [ float(minFreq) / float(1E6) + i * freqDelta for i in range(0, nSteps)]
    plt.figure(figsize=(6, 4))
    plt.scatter(freqArray, spectrumData)
    plt.xlabel("Freq (MHz)")
    plt.ylabel("Power (dBm)")
    locationMessage = db.locationMessages.find_one({"_id": ObjectId(msg["locationMessageId"])})
    t = msg["t"] + milisecOffset / float(1000)
    tz = locationMessage[TIME_ZONE_KEY]
    plt.title("Spectrum at " + timezone.formatTimeStampLong(t, tz))
    spectrumFile = sessionId + "/" + msg[SENSOR_ID] + "." + str(startTime) + "." + str(milisecOffset) + ".spectrum.png"
    spectrumFilePath = util.getPath("static/generated/") + spectrumFile
    plt.savefig(spectrumFilePath, pad_inches=0, dpi=100)
    plt.clf()
    plt.close()
    # plt.close("all")
    retval = {"spectrum" : spectrumFile }
    util.debugPrint(retval)
    return jsonify(retval)




######################################################################################

@app.route("/api/<path:path>",methods=["GET"])
@app.route("/generated/<path:path>", methods=["GET"])
@app.route("/myicons/<path:path>", methods=["GET"])
@app.route("/spectrumbrowser/<path:path>", methods=["GET"])
def getScript(path):
    util.debugPrint("getScript()")
    p = urlparse.urlparse(request.url)
    urlpath = p.path
    return app.send_static_file(urlpath[1:])


@app.route("/", methods=["GET"])
def root():
    util.debugPrint("root()")
    return app.send_static_file("app.html")


@app.route("/spectrumbrowser/authenticate/<privilege>/<userName>", methods=['POST'])
def authenticate(privilege, userName):
    """

    Authenticate the user given his username and password at the requested privilege or return
    error if the user cannot be authenticated.

    URL Path:

    - privilege : Desired privilege (user or admin).
    - userName : user login name.
    - sessionId : The login session ID to be used for subsequent interactions
            with this service.
    URL Args:

    - None

    Return codes:

    - 200 OK if authentication is OK
            On success, a JSON document with the following information is returned.
    - 403 Forbidden if authentication fails.

    """
    password = request.args.get("password", None)
    return authentication.authenticateUser(privilege,userName,password)


@app.route("/spectrumbrowser/getLocationInfo/<sessionId>", methods=["POST"])
def getLocationInfo(sessionId):
    """

    Get the location and system messages for all sensors.

    URL Path:

    - sessionid : The session ID for the login session.

    URL Args:

    - None

    HTTP return codes:

        - 200 OK if the call completed successfully.
        On success this returns a JSON formatted document
        containing a list of all the System and Location messages
        in the database. Additional information is added to the
        location messages (i.e.  the supported frequency bands of
        the sensor). Sensitive information such as sensor Keys are
        removed from the returned document.  Please see the MSOD
        specification for documentation on the format of these JSON
        messages. This API is used to populate the top level view (the map)
        that summarizes the data. Shown below is an example interaction
        (consult the MSOD specification for details):

        Request:

        ::

           curl -X POST http://localhost:8000/spectrumbrowser/getLocationInfo/guest-123

        Returns the following jSON document:

        ::

            {
                "locationMessages": [
                    {
                    "Alt": 143.5,
                    "Lat": 39.134374999999999,
                    "Lon": -77.215337000000005,
                    "Mobility": "Stationary",
                    "SensorID": "ECR16W4XS",
                    "TimeZone": "America/New_York",
                    "Type": "Loc",
                    "Ver": "1.0.9",
                    "sensorFreq": [ # An array of frequency bands supported (inferred
                                    # from the posted data messages)
                        "703967500:714047500",
                        "733960000:744040000",
                        "776967500:787047500",
                        "745960000:756040000"
                    ],
                    "t": 1404964924,
                    "tStartLocalTime": 1404950524,
                    }, ....
                ],
                "systemMessages": [
                {
                    "Antenna": {
                    "Model": "Unknown (whip)",
                    "Pol": "VL",
                    "VSWR": "NaN",
                    "XSD": "NaN",
                    "bwH": 360.0,
                    "bwV": "NaN",
                    "fHigh": "NaN",
                    "fLow": "NaN",
                    "gAnt": 2.0,
                    "lCable": 0.5,
                    "phi": 0.0,
                    "theta": "N/A"
                    }
                "COTSsensor": {
                    "Model": "Ettus USRP N210 SBX",
                    "fMax": 4400000000.0,
                    "fMin": 400000000.0,
                    "fn": 5.0,
                    "pMax": -10.0
                },
                "Cal": "N/A",
                "Preselector": {
                    "enrND": "NaN",
                    "fHighPassBPF": "NaN",
                    "fHighStopBPF": "NaN",
                    "fLowPassBPF": "NaN",
                    "fLowStopBPF": "NaN",
                    "fnLNA": "NaN",
                    "gLNA": "NaN",
                    "pMaxLNA": "NaN"
                },
                "SensorID": "ECR16W4XS",
                "Type": "Sys",
                "Ver": "1.0.9",
                "t": 1404964924
                },....
            ]
            }

        - 403 Forbidden if the session ID is not found.

    """
    try:
        if not checkSessionId(sessionId):
            abort(403)
        return GetLocationInfo.getLocationInfo()
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise



@app.route("/spectrumbrowser/getDailyMaxMinMeanStats/<sensorId>/<startTime>/<dayCount>/<fmin>/<fmax>/<sessionId>", methods=["POST"])
def getDailyStatistics(sensorId, startTime, dayCount, fmin, fmax, sessionId):
    """

    Get the daily statistics for the given start time, frequency band and day count for a given sensor ID

    URL Path:

    - sensorId: The sensor ID of interest.
    - startTime: The start time in the UTC time zone specified as a second offset from 1.1.1970:0:0:0 (UTC).
    - dayCount : The number days for which we want the statistics.
    - sessionId : The session ID of the login session.
    - fmin : min freq in MHz of the band of interest.
    - fmax : max freq in MHz of the band of interest.
    - sessionId: login session ID.

    URL args (optional):

    - subBandMinFreq : the min freq of the sub band of interest (contained within a band supported by the sensor).
    - subBandMaxFreq: the max freq of the sub band of interest (contained within a band supported by the sensor).

    If the URL args are not specified, the entire frequency band is used for computation.

    HTTP return codes:

    - 200 OK if the call returned without errors.
        Returns a JSON document containing the daily statistics for the queried sensor returned as an array of JSON
        records. Here is an example interaction (using UNIX curl to send the request):

    Request:

    ::

        curl -X POST http://localhost:8000/spectrumbrowser/getDailyMaxMinMeanStats/ECR16W4XS/1404907200/5/745960000/756040000/guest-123

    Which returns the following response (annotated and abbreviated):

    ::

        {
        "channelCount": 56, # The number of channels
        "cutoff": -75.0,    # The cutoff for occupancy computations.
        "maxFreq": 756040000.0, # Max band freq. in Hz.
        "minFreq": 745960000.0, # Min band freq in Hz.
        "startDate": "2014-07-09 00:00:00 EDT", # The formatted time stamp.
        "tmin": 1404892800, # The universal time stamp.
        "values": {
            "0": {          # The hour offset from start time.
                "maxOccupancy": 0.05, # Max occupancy
                "meanOccupancy": 0.01,# Mean occupancy
                "minOccupancy": 0.01  # Min occupancy.
            }, ... # There is an array of such structures

        }
        }


    - 403 Forbidden if the session ID was not found.
    - 404 Not Found if the sensor data was not found.

    """
    try:
        util.debugPrint("getDailyMaxMinMeanStats : " + sensorId + " " + startTime + " " + dayCount)
        if not checkSessionId(sessionId):
           abort(403)
        subBandMinFreq = int(request.args.get("subBandMinFreq", fmin))
        subBandMaxFreq = int(request.args.get("subBandMaxFreq", fmax))
        return GetDailyMaxMinMeanStats.getDailyMaxMinMeanStats(sensorId, startTime, dayCount, fmin, fmax,subBandMinFreq,subBandMaxFreq, sessionId)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise



@app.route("/spectrumbrowser/getDataSummary/<sensorId>/<lat>/<lon>/<alt>/<sessionId>", methods=["POST"])
def getDataSummary(sensorId, lat, lon, alt, sessionId):
    """

    Get the sensor data summary  for the sensor given its ID, latitude and longitude.

    URL Path:

    - sensorId: Sensor ID of interest.
    - lat : Latitude
    - lon: Longitude
    - alt: Altitude
    - sessionId : Login session ID

    URL args (optional):

    - minFreq : Min band frequency of a band supported by the sensor.
            if this parameter is not specified then the min freq of the sensor is used.
    - maxFreq : Max band frequency of a band supported by the sensor.
            If this parameter is not specified, then the max freq of the sensor is used.
    - minTime : Universal start time (seconds) of the interval we are
            interested in. If this parameter is not specified, then the acquisition
            start time is used.
    - dayCount : The number of days for which we want the data. If this
            parameter is not specified, then the interval from minTime to the end of the
            available data is used.

    HTTP return codes:

    - 200 OK Success. Returns a JSON document with a summary of the available
    data in the time range and frequency band of interest.
    Here is an example Request using the unix curl command:

    ::

        curl -X POST http://localhost:8000/spectrumbrowser/getDataSummary/Cotton1/40/-105.26/1676/guest-123

    Here is an example of the JSON document (annotated) returned in response :

    ::

        {
          "maxFreq": 2899500000, # max Freq the band of interest for the sensor (hz)
          "minFreq": 2700500000, # min freq of the band of interest for  sensor (hz)
          "maxOccupancy": 1.0, # max occupancy
          "meanOccupancy": 0.074, # Mean Occupancy
          "minOccupancy": 0.015, # Min occupancy
          "measurementType": "Swept-frequency",# Measurement type
          "readingsCount": 882, # acquistion count in interval of interest.
          "tAquisitionEnd": 1403899158, # Timestamp (universal time) for end acquisition
                                        # in interval of interest.
          "tAquisitionEndFormattedTimeStamp": "2014-06-27 09:59:18 MDT", #Formatted timestamp
                                                                         #for end acquistion
          "tAquistionStart": 1402948665, # universal timestamp for start of acquisition
          "tAquisitionStartFormattedTimeStamp": "2014-06-16 09:57:45 MDT",# Formatted TS for start of acq.
          "tEndReadings": 1403899158, # universal Timestamp for end of available readings.
          "tEndDayBoundary": 1403863200, # Day boundary of the end of available data (i.e 0:0:0 next day)
          "tEndReadingsLocalTime": 1403877558.0, # Local timestamp for end of readings.
          "tEndLocalTimeFormattedTimeStamp": "2014-06-27 09:59:18 MDT", # formatted TS for end of interval.
          "tStartReadings": 1402948665  # universal timestamp for start of available readings.
          "tStartDayBoundary": 1402912800.0, # Day boundary (0:0:0 next day) timestamp
                                             # for start of available readings.
          "tStartLocalTime": 1402927065, # Local timestamp for start of available readings
          "tStartLocalTimeFormattedTimeStamp": "2014-06-16 09:57:45 MDT", # formatted timestamp for the
                                                                          # start of interval of interest.
          }

    - 403 Forbidden if the session ID is not recognized.
    - 404 Not Found if the location message for the sensor ID is not found.

    """

    util.debugPrint("getDataSummary")
    try:
        if not checkSessionId(sessionId):
            util.debugPrint("SessionId not found")
            abort(403)
        longitude = float(lon)
        latitude = float(lat)
        alt = float(alt)
        locationMessage = db.locationMessages.find_one({SENSOR_ID:sensorId, "Lon":longitude, "Lat":latitude, "Alt":alt})
        if locationMessage == None:
            util.debugPrint("Location Message not found")
            abort(404)

        locationMessageId = str(locationMessage["_id"])
        # min and specifies the freq band of interest. If nothing is specified or the freq is -1,
        # then all frequency bands are queried.
        minFreq = int (request.args.get("minFreq", "-1"))
        maxFreq = int(request.args.get("maxFreq", "-1"))
        if minFreq != -1 and maxFreq != -1 :
            freqRange = populate_db.freqRange(minFreq, maxFreq)
        else:
            freqRange = None
        # tmin and tmax specify the min and the max values of the time range of interest.
        tmin = request.args.get('minTime', '')
        dayCount = request.args.get('dayCount', '')
        tzId = locationMessage[TIME_ZONE_KEY]
        if freqRange == None:
            if tmin == '' and dayCount == '':
                query = { SENSOR_ID: sensorId, "locationMessageId":locationMessageId }
            elif tmin != ''  and dayCount == '' :
                mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin), tzId)
                query = { SENSOR_ID:sensorId, "locationMessageId":locationMessageId, "t" : {'$gte':mintime} }
            else:
                mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin), tzId)
                maxtime = mintime + int(dayCount) * SECONDS_PER_DAY
                query = { SENSOR_ID: sensorId, "locationMessageId":locationMessageId, "t": { '$lte':maxtime, '$gte':mintime}  }
        else :
            if tmin == '' and dayCount == '':
                query = { SENSOR_ID: sensorId, "locationMessageId":locationMessageId, "freqRange": freqRange }
            elif tmin != ''  and dayCount == '' :
                mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin), tzId)
                query = { SENSOR_ID:sensorId, "locationMessageId":locationMessageId, "t" : {'$gte':mintime}, "freqRange":freqRange }
            else:
                mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(int(tmin), tzId)
                maxtime = mintime + int(dayCount) * SECONDS_PER_DAY
                query = { SENSOR_ID: sensorId, "locationMessageId":locationMessageId, "t": { '$lte':maxtime, '$gte':mintime} , "freqRange":freqRange }

        util.debugPrint(query)
        cur = db.dataMessages.find(query)
        if cur == None:
            errorStr = "No data found"
            response = make_response(util.formatError(errorStr), 404)
            return response
        nreadings = cur.count()
        if nreadings == 0:
            util.debugPrint("No data found. zero cur count.")
            del query['t']
            msg = db.dataMessages.find_one(query)
            if msg != None:
                tStartDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg["t"], tzId)
                if dayCount == '':
                    query["t"] = {"$gte":tStartDayBoundary}
                else:
                    maxtime = tStartDayBoundary + int(dayCount) * SECONDS_PER_DAY
                    query["t"] = {"$gte":tStartDayBoundary, "$lte":maxtime}
                cur = db.dataMessages.find(query)
                nreadings = cur.count()
            else :
                errorStr = "No data found"
                response = make_response(util.formatError(errorStr), 404)
                return response
        util.debugPrint("retrieved " + str(nreadings))
        cur.batch_size(20)
        minOccupancy = 10000
        maxOccupancy = -10000
        maxFreq = 0
        minFreq = -1
        meanOccupancy = 0
        minTime = time.time() + 10000
        minLocalTime = time.time() + 10000
        maxTime = 0
        measurementType = "UNDEFINED"
        lastMessage = None
        tStartDayBoundary = 0
        tStartLocalTimeTzName = None
        for msg in cur:
            if tStartDayBoundary == 0 :
                tStartDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg["t"], tzId)
                (minLocalTime, tStartLocalTimeTzName) = timezone.getLocalTime(msg['t'], tzId)
            if msg["mType"] == "FFT-Power" :
                minOccupancy = np.minimum(minOccupancy, msg["minOccupancy"])
                maxOccupancy = np.maximum(maxOccupancy, msg["maxOccupancy"])
            else:
                minOccupancy = np.minimum(minOccupancy, msg["occupancy"])
                maxOccupancy = np.maximum(maxOccupancy, msg["occupancy"])
            maxFreq = np.maximum(msg["mPar"]["fStop"], maxFreq)
            if minFreq == -1 :
                minFreq = msg["mPar"]["fStart"]
            else:
                minFreq = np.minimum(msg["mPar"]["fStart"], minFreq)
            if "meanOccupancy" in msg:
                meanOccupancy += msg["meanOccupancy"]
            else:
                meanOccupancy += msg["occupancy"]
            minTime = np.minimum(minTime, msg["t"])
            maxTime = np.maximum(maxTime, msg["t"])
            measurementType = msg["mType"]
            lastMessage = msg
        (tEndReadingsLocalTime, tEndReadingsLocalTimeTzName) = timezone.getLocalTime(lastMessage['t'], tzId)
        tEndDayBoundary = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(lastMessage["t"], tzId)
        # now get the global min and max time of the aquistions.
        if 't' in query:
            del query['t']
        cur = db.dataMessages.find(query)
        firstMessage = cur.next()
        cur = db.dataMessages.find(query)
        sortedCur = cur.sort('t', pymongo.DESCENDING).limit(10)
        lastMessage = sortedCur.next()
        tAquisitionStart = firstMessage['t']
        tAquisitionEnd = lastMessage['t']
        tAquisitionStartFormattedTimeStamp = timezone.formatTimeStampLong(tAquisitionStart, tzId)
        tAquisitionEndFormattedTimeStamp = timezone.formatTimeStampLong(tAquisitionEnd, tzId)
        meanOccupancy = meanOccupancy / nreadings
        retval = {"minOccupancy":minOccupancy, \
            "tAquistionStart": tAquisitionStart, \
            "tAquisitionStartFormattedTimeStamp": tAquisitionStartFormattedTimeStamp, \
            "tAquisitionEnd":tAquisitionEnd, \
            "tAquisitionEndFormattedTimeStamp": tAquisitionEndFormattedTimeStamp, \
            "tStartReadings":minTime, \
            "tStartLocalTime": minLocalTime, \
            "tStartLocalTimeFormattedTimeStamp" : timezone.formatTimeStampLong(minTime, tzId), \
            "tStartDayBoundary":float(tStartDayBoundary), \
            "tEndReadings":float(maxTime), \
            "tEndReadingsLocalTime":float(tEndReadingsLocalTime), \
            "tEndLocalTimeFormattedTimeStamp" : timezone.formatTimeStampLong(maxTime, tzId), \
            "tEndDayBoundary":float(tEndDayBoundary), \
            "maxOccupancy":util.roundTo3DecimalPlaces(maxOccupancy), \
            "meanOccupancy":util.roundTo3DecimalPlaces(meanOccupancy), \
            "maxFreq":maxFreq, \
            "minFreq":minFreq, \
            "measurementType": measurementType, \
            "readingsCount":float(nreadings)}
        print retval
        return jsonify(retval)
    except :
         print "Unexpected error:", sys.exc_info()[0]
         print sys.exc_info()
         traceback.print_exc()



@app.route("/spectrumbrowser/getOneDayStats/<sensorId>/<startTime>/<minFreq>/<maxFreq>/<sessionId>", methods=["POST"])
def getOneDayStats(sensorId, startTime, minFreq, maxFreq, sessionId):
    """

    Get the statistics for a given sensor given a start time for a single day of data.
    The time is rounded to the start of the day boundary.
    Times for this API are specified as the time in the UTC time domain as a second offset from 1.1.1970:0:0:0
    (i.e. universal time; not local time)

    URL Path:

    - sensorId: Sensor ID for the sensor of interest.
    - startTime: start time within the day boundary of the acquisitions of interest.
    - minFreq: Minimum Frequency in MHz of the band of interest.
    - maxFreq: Maximum Frequency in MHz of the band of interest.
    - sessionId: login Session ID.

    URL Args:

    - None

    HTTP Return Codes:

    - 200 OK on success. Returns a JSON document with the path to the generated image of the spectrogram.
    - 403 Forbidden if the session ID was not found.
    - 404 Not found if the data was not found.

    """
    if not checkSessionId(sessionId):
       util.debugPrint("SessionId not found")
       abort(403)
    minFreq = int(minFreq)
    maxFreq = int(maxFreq)
    freqRange = populate_db.freqRange(minFreq, maxFreq)
    mintime = int(startTime)
    maxtime = mintime + SECONDS_PER_DAY
    query = { SENSOR_ID: sensorId, "t": { '$lte':maxtime, '$gte':mintime}, "freqRange":freqRange  }
    util.debugPrint(query)
    msg = db.dataMessages.find_one(query)
    query = { "_id": ObjectId(msg["locationMessageId"]) }
    locationMessage = db.locationMessages.find_one(query)
    mintime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(msg["t"], locationMessage[TIME_ZONE_KEY])
    maxtime = mintime + SECONDS_PER_DAY
    query = { SENSOR_ID: sensorId, "t": { '$lte':maxtime, '$gte':mintime} , "freqRange":freqRange }
    cur = db.dataMessages.find(query)
    if cur == None:
        abort(404)
    res = {}
    values = {}
    res["formattedDate"] = timezone.formatTimeStampLong(mintime, locationMessage[TIME_ZONE_KEY])
    for msg in cur:
        channelCount = msg["mPar"]["n"]
        cutoff = msg["cutoff"]
        values[msg["t"] - mintime] = {"t": msg["t"], \
                        "maxPower" : msg["maxPower"], \
                        "minPower" : msg["minPower"], \
                        "maxOccupancy":util.roundTo3DecimalPlaces(msg["maxOccupancy"]), \
                        "minOccupancy":util.roundTo3DecimalPlaces(msg["minOccupancy"]), \
                        "meanOccupancy":util.roundTo3DecimalPlaces(msg["meanOccupancy"]), \
                        "medianOccupancy":util.roundTo3DecimalPlaces(msg["medianOccupancy"])}
    res["channelCount"] = channelCount
    res["cutoff"] = cutoff
    res["values"] = values
    return jsonify(res)


@app.route("/spectrumbrowser/generateSingleAcquisitionSpectrogramAndOccupancy/<sensorId>/<startTime>/<minFreq>/<maxFreq>/<sessionId>", methods=["POST"])
def generateSingleAcquisitionSpectrogram(sensorId, startTime, minFreq, maxFreq, sessionId):
    """

    Generate the single acquisiton spectrogram image for FFT-Power readings. The
    spectrogram is used by the GUI to put up an image of the spectrogram.
    This API also returns the occupancy array for the generated image.
    An image for the spectrogram is generated by the server and a path
    to that image is returned.  Times for this API are specified as the
    time in the UTC time domain (universal time not local time) as a second offset from
    1.1.1970:0:0:0 UTC time.

    URL Path:

        - sensorId is the sensor ID of interest.
        - startTime - the acquisition  time stamp  for the data message for FFT power.
        - minFreq - The minimum frequency of the frequency band of interest.
        - maxFreq - The maximum frequency of the frequency band of interest.
        - sessionId - Login session Id.

    HTTP Return codes:

       - 200 OK On Success this returns a JSON document containing the following information.
            - "spectrogram": File resource containing the generated spectrogram.
            - "cbar": path to the colorbar for the spectrogram.
            - "maxPower": Max power for the spectrogram
            - "minPower": Min power for the spectrogram.
            - "cutoff": Power cutoff for occupancy.
            - "noiseFloor" : Noise floor.
            - "maxFreq": max frequency for the spectrogram.
            - "minFreq": minFrequency for the spectrogram.
            - "minTime": min time for the spectrogram.
            - "timeDelta": Time delta for the spectrogram window.
            - "prevAcquisition" : Time of the previous acquistion (or -1 if no acquistion exists).
            - "nextAcquisition" : Time of the next acquistion (or -1 if no acquistion exists).
            - "formattedDate" : Formatted date for the aquisition.
            - "image_width": Image width of generated image (pixels).
            - "image_height": Image height of generated image (pixels).
            - "timeArray" : Time array for occupancy returned as offsets from the start time of the acquistion.
            - "occpancy" : Occupancy occupancy for each spectrum of the spectrogram. This is returned as a one dimensional array.
            Each occupancy point in the array corresponds to the time offset recorded in the time array.
       - 403 Forbidden if the session ID is not recognized.
       - 404 Not Found if the message for the given time is not found.

    """
    try:
        if not checkSessionId(sessionId):
            abort(403)
        startTimeInt = int(startTime)
        minfreq = int(minFreq)
        maxfreq = int(maxFreq)
        query = { SENSOR_ID: sensorId}
        msg = db.dataMessages.find_one(query)
        if msg == None:
            util.debugPrint("Sensor ID not found " + sensorId)
            abort(404)
        if msg["mType"] == "FFT-Power":
            query = { SENSOR_ID: sensorId, "t": startTimeInt, "freqRange": populate_db.freqRange(minfreq, maxfreq)}
            util.debugPrint(query)
            msg = db.dataMessages.find_one(query)
            if msg == None:
                errorStr = "Data message not found for " + startTime
                util.debugPrint(errorStr)
                response = make_response(util.formatError(errorStr), 404)
                return response
            result = generateSingleAcquisitionSpectrogramAndOccupancyForFFTPower(msg, sessionId)
            if result == None:
                errorStr = "Illegal Request"
                response = make_response(util.formatError(errorStr), 400)
                return response
            else:
                return result
        else :
           util.debugPrint("Only FFT-Power type messages supported")
           errorStr = "Illegal Request"
           response = make_response(util.formatError(errorStr), 400)
           return response
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise

@app.route("/spectrumbrowser/generateSingleDaySpectrogramAndOccupancy/<sensorId>/<startTime>/<minFreq>/<maxFreq>/<sessionId>", methods=["POST"])
def generateSingleDaySpectrogram(sensorId, startTime, minFreq, maxFreq, sessionId):
    """

    Generate a single day spectrogram for Swept Frequency measurements as an image on the server.

    URL Path:

    - sensorId: The sensor ID of interest.
    - startTime: The start time in UTC as a second offset from 1.1.1970:0:0:0 in the UTC time zone.
    - minFreq: the min freq of the band of interest.
    - maxFreq: the max freq of the band of interest.
    - sessionId: The login session ID.

    URL Args:

    - subBandMinFreq : Sub band minimum frequency (should be contained in a frequency band supported by the sensor).
    - subBandMaxFreq : Sub band maximum frequency (should be contained in a frequency band supported by the sensor).

    HTTP Return Codes:

    - 403 Forbidden if the session ID is not found.
    - 200 OK if success. Returns a JSON document with a path to the generated spectrogram (which can be later used to access the image).

    """
    try:
        if not checkSessionId(sessionId):
            abort(403)
        startTimeInt = int(startTime)
        minfreq = int(minFreq)
        maxfreq = int(maxFreq)
        print request
        subBandMinFreq = int(request.args.get("subBandMinFreq", minFreq))
        subBandMaxFreq = int(request.args.get("subBandMaxFreq", maxFreq))
        query = { SENSOR_ID: sensorId}
        msg = db.dataMessages.find_one(query)
        if msg == None:
            util.debugPrint("Sensor ID not found " + sensorId)
            abort(404)
            query = { SENSOR_ID: sensorId, "t":{"$gte" : startTimeInt}, "freqRange":populate_db.freqRange(minfreq, maxfreq)}
            util.debugPrint(query)
            msg = db.dataMessages.find_one(query)
            if msg == None:
                errorStr = "Data message not found for " + startTime
                util.debugPrint(errorStr)
                return make_response(util.formatError(errorStr), 404)
        if msg["mType"] == "Swept-frequency" :
            return generateSingleDaySpectrogramAndOccupancyForSweptFrequency(msg, sessionId, startTimeInt, minfreq, maxfreq, subBandMinFreq, subBandMaxFreq)
        else:
            errorStr = "Illegal message type"
            util.debugPrint(errorStr)
            return make_response(util.formatError(errorStr), 400)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise



@app.route("/spectrumbrowser/generateSpectrum/<sensorId>/<start>/<timeOffset>/<sessionId>", methods=["POST"])
def generateSpectrum(sensorId, start, timeOffset, sessionId):
    """

    Generate the spectrum image for a given start time and time offset from that start time.

    URL Path:

    - sensorId: Sensor ID of interest.
    - start: start time in the UTC time zone as an offset from 1.1.1970:0:0:0 UTC.
    - timeOffset: time offset from the start time in seconds.
    - sessionId: The session ID of the login session.

    URL Args: None

    HTTP return codes:
    - 403 Forbidden if the session ID is not recognized.
    - 200 OK if the request was successfully processed.
      Returns a JSON document with a URI to the generated image.

    """
    try:
        if not checkSessionId(sessionId):
            abort(403)
        startTime = int(start)
        # get the type of the measurement.
        msg = db.dataMessages.find_one({SENSOR_ID:sensorId})
        if msg["mType"] == "FFT-Power":
            msg = db.dataMessages.find_one({SENSOR_ID:sensorId, "t":startTime})
            if msg == None:
                errorStr = "dataMessage not found "
                util.debugPrint(errorStr)
                abort(404)
            milisecOffset = int(timeOffset)
            return generateSpectrumForFFTPower(msg, milisecOffset, sessionId)
        else :
            secondOffset = int(timeOffset)
            time = secondOffset + startTime
            print "time " , time
            time = secondOffset + startTime
            msg = db.dataMessages.find_one({SENSOR_ID:sensorId, "t":{"$gte": time}})
            minFreq = int(request.args.get("subBandMinFrequency", msg["mPar"]["fStart"]))
            maxFreq = int(request.args.get("subBandMaxFrequency", msg["mPar"]["fStop"]))
            if msg == None:
                errorStr = "dataMessage not found "
                util.debugPrint(errorStr)
                abort(404)
            return generateSpectrumForSweptFrequency(msg, sessionId, minFreq, maxFreq)
    except:
         print "Unexpected error:", sys.exc_info()[0]
         print sys.exc_info()
         traceback.print_exc()
         raise

@app.route("/spectrumbrowser/generateZipFileFileForDownload/<sensorId>/<startTime>/<days>/<minFreq>/<maxFreq>/<sessionId>", methods=["POST"])
def generateZipFileForDownload(sensorId, startTime, days, minFreq, maxFreq, sessionId):
    """

    Generate a Zip file file for download.

    URL Path:

    - sensorId : The sensor ID of interest.
    - startTime : Start time as a second offset from 1.1.1970:0:0:0 UTC in the UTC time Zone.
    - minFreq : Min freq of the band of interest.
    - maxFreq : Max Freq of the band of interest.
    - sessionId : Login session ID.

    URL Args:

    - None.

    HTTP Return Codes:

    - 200 OK successful execution. A JSON document containing a path to the generated Zip file is returned.
    - 403 Forbidden if the sessionId is invalid.
    - 404 Not found if the requested data was not found.

    """
    try:
        if not checkSessionId(sessionId):
            abort(403)
        return GenerateZipFileForDownload.generateZipFileForDownload(sensorId, startTime, days, minFreq, maxFreq, sessionId)
    except:
         print "Unexpected error:", sys.exc_info()[0]
         print sys.exc_info()
         traceback.print_exc()
         raise

@app.route("/spectrumbrowser/emailDumpUrlToUser/<emailAddress>/<sessionId>", methods=["POST"])
def emailDumpUrlToUser(emailAddress, sessionId):
    """

    Send email to the given user when his requested dump file becomes available.

    URL Path:

    - emailAddress : The email address of the user.
    - sessionId : the login session Id of the user.

    URL Args (required):

    - urlPrefix : The url prefix that the web browser uses to access the data later (after the zip has been generated).
    - uri : The path used to access the zip file (previously returned from GenerateZipFileForDownload).

    HTTP Return Codes:

    - 200 OK : if the request successfully completed.
    - 403 Forbidden : Invalid session ID.
    - 400 Bad Request: URL args not present or invalid.

    """
    try:
        if not checkSessionId(sessionId):
            abort(403)
        urlPrefix = request.args.get("urlPrefix", None)
        util.debugPrint(urlPrefix)
        uri = request.args.get("uri", None)
        util.debugPrint(uri)
        if urlPrefix == None or uri == None :
            abort(400)
        url = urlPrefix + uri
        return GenerateZipFileForDownload.emailDumpUrlToUser(emailAddress, url, uri)
    except:
         print "Unexpected error:", sys.exc_info()[0]
         print sys.exc_info()
         traceback.print_exc()
         raise

@app.route("/spectrumbrowser/checkForDumpAvailability/<sessionId>", methods=["POST"])
def checkForDumpAvailability(sessionId):
    """

    Check for availability of a previously generated dump file.

    URL Path:

    - sessionId: The session ID of the login session.

    URL Args (required):

    - uri : A URI pointing to the generated file to check for.

    HTTP Return Codes:

    - 200 OK if success
      Returns a json document {status: OK} file exists.
      Returns a json document {status:NOT_FOUND} if the file does not exist.
    - 400 Bad request. If the URL args are not present.
    - 403 Forbidden if the sessionId is invalid.

    """
    try:
        if not checkSessionId(sessionId):
            abort(403)
        uri = request.args.get("uri", None)
        util.debugPrint(uri)
        if  uri == None :
            util.debugPrint("URI not specified.")
            abort(400)
        if  GenerateZipFileForDownload.checkForDumpAvailability(uri):
            return jsonify({"status":"OK"})
        else:
            return jsonify({"status":"NOT_FOUND"})
    except:
         print "Unexpected error:", sys.exc_info()[0]
         print sys.exc_info()
         traceback.print_exc()
         raise


@app.route("/spectrumbrowser/generatePowerVsTime/<sensorId>/<startTime>/<freq>/<sessionId>", methods=["POST"])
def generatePowerVsTime(sensorId, startTime, freq, sessionId):
    """

    URL Path:

    - sensorId : the sensor ID of interest.
    - startTime: The start time of the aquisition.
    - freq : The frequency of interest.

    URL Args:

    - None

    HTTP Return Codes:

    - 200 OK. Returns a JSON document containing the path to the generated image.
    - 404 Not found. If the aquisition was not found.

    """
    try:
        if not checkSessionId(sessionId):
            abort(403)
        msg = db.dataMessages.find_one({SENSOR_ID:sensorId})
        if msg == None:
            util.debugPrint("Message not found")
            abort(404)
        if msg["mType"] == "FFT-Power":
            msg = db.dataMessages.find_one({SENSOR_ID:sensorId, "t":int(startTime)})
            if msg == None:
                errorMessage = "Message not found"
                util.debugPrint(errorMessage)
                abort(404)
            freqHz = int(freq)
            return GeneratePowerVsTime.generatePowerVsTimeForFFTPower(msg, freqHz, sessionId)
        else:
            msg = db.dataMessages.find_one({SENSOR_ID:sensorId, "t": {"$gt":int(startTime)}})
            if msg == None:
                errorMessage = "Message not found"
                util.debugPrint(errorMessage)
                abort(404)
            freqHz = int(freq)
            return GeneratePowerVsTime.generatePowerVsTimeForSweptFrequency(msg, freqHz, sessionId)
    except:
         print "Unexpected error:", sys.exc_info()[0]
         print sys.exc_info()
         traceback.print_exc()
         raise

@app.route("/spectrumdb/upload", methods=["POST"])
def upload() :
    """

    Upload sensor data to the database. The format is as follows:

        lengthOfDataMessageHeader<CRLF>DataMessageHeader Data

    Note that the data should immediately follow the DataMessage header (no space or CRLF).

    URL Path:

    - None

    URL Parameters:

    - None.

    Return Codes:

    - 200 OK if the data was successfully put into the MSOD database.
    - 403 Forbidden if the sensor key is not recognized.

    """
    msg = request.data
    sensorId = msg[SENSOR_ID]
    key = msg["SensorKey"]
    if not authentication.authenticateSensor(sensorId,key):
        abort(403)
    populate_db.put_message(msg)
    return "OK"


@sockets.route("/sensordata", methods=["POST", "GET"])
def getSensorData(ws):
    """

    Handle sensor data streaming requests.

    """
    try :
        print "getSensorData"
        token = ws.receive()
        print "token = " , token
        parts = token.split(":")
        sessionId = parts[0]
        if not checkSessionId(sessionId):
            ws.close()
            return
        sensorId = parts[1]
        util.debugPrint("sensorId " + sensorId)
        if not sensorId in lastDataMessage :
            ws.send(dumps({"status":"NO_DATA"}))
        else:
            ws.send(dumps({"status":"OK"}))
            ws.send(lastDataMessage[sensorId])
            lastdatatime = -1
            while True:
                if lastdatatime != lastdataseen[sensorId]:
                    lastdatatime = lastdataseen[sensorId]
                    ws.send(sensordata[sensorId])
                gevent.sleep(SECONDS_PER_FRAME)
    except:
        ws.close()
        print "Error writing to websocket"


@sockets.route("/spectrumdb/stream", methods=["POST"])
def datastream(ws):
    print "Got a connection"
    bbuf = MyByteBuffer(ws)
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
        print dumps(jsonData, sort_keys=True, indent=4)
        if jsonData["Type"] == "Data":
            td = jsonData["mPar"]["td"]
            nM = jsonData["nM"]
            n = jsonData["mPar"]["n"]
            sensorId = jsonData["SensorID"]
            lastDataMessage[sensorId] = jsonStringBytes
            timePerMeasurement = float(td) / float(nM)
            spectrumsPerFrame = int(SECONDS_PER_FRAME / timePerMeasurement)
            measurementsPerFrame = spectrumsPerFrame * n
            util.debugPrint("measurementsPerFrame : " + str(measurementsPerFrame) + " n = " + str(n) + " spectrumsPerFrame = " + str(spectrumsPerFrame))
            while True:
                startTime = time.time()
                if peakDetection:
                    powerVal = [-100 for i in range(0, n)]
                else:
                    powerVal = [0 for i in range(0, n)]
                for i in range(0, measurementsPerFrame):
                    data = bbuf.readByte()
                    if peakDetection:
                        powerVal[i % n] = np.maximum(powerVal[i % n], data)
                    else:
                        powerVal[i % n] += data
                if not peakDetection:
                    for i in range(0, len(powerVal)):
                        powerVal[i] = powerVal[i] / spectrumsPerFrame
                # sending data as CSV values.
                sensordata[sensorId] = str(powerVal)[1:-1].replace(" ", "")
                lastdataseen[sensorId] = time.time()
                endTime = time.time()
                delta = 0.7 * SECONDS_PER_FRAME - endTime + startTime
                if delta > 0:
                    gevent.sleep(delta)
                else:
                    gevent.sleep(0.7 * SECONDS_PER_FRAME)
                # print "count " , count
        elif jsonData["Type"] == "Sys":
            print "Got a System message"
        elif jsonData["Type"] == "Loc":
            print "Got a Location Message"

@sockets.route("/spectrumdb/test", methods=["POST"])
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
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        raise

@app.route("/spectrumbrowser/log", methods=["POST"])
def log():
    if debug:
        data = request.data
        jsonValue = json.loads(data)
        message = jsonValue["message"]
        print "Log Message : " + message
        exceptionInfo = jsonValue["ExceptionInfo"]
        if len(exceptionInfo) != 0 :
            print "Exception Info:"
            for i in range(0, len(exceptionInfo)):
                print "Exception Message:"
                exceptionMessage = exceptionInfo[i]["ExceptionMessage"]
                print "Stack Trace :"
                stackTrace = exceptionInfo[i]["StackTrace"]
                print exceptionMessage
                util.decodeStackTrace(stackTrace)
    return "OK"

# @app.route("/spectrumbrowser/login", methods=["POST"])
# def login() :
#    sessionId = random.randint(0,1000)
#    returnVal = {}
#    returnVal["status"] = "OK"
#    returnVal["sessionId"] = sessionId
#    secureSessions[request.remote_addr] = sessionId
#    return JSONEncoder().encode(returnVal)


if __name__ == '__main__':
    launchedFromMain = True
    util.loadGwtSymbolMap()
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    # app.run('0.0.0.0',port=8000,debug="True")
    server = pywsgi.WSGIServer(('0.0.0.0', 8000), app, handler_class=WebSocketHandler)
    server.serve_forever()

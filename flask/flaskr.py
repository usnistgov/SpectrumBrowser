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
from mpl_toolkits.axes_grid1 import make_axes_locatable
import gridfs
import ast
import datetime
import pytz
import calendar




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

def getTimeStamp(timeStamp,timeZoneId):
    retval=  int(time.mktime(datetime.datetime.fromtimestamp(float(timeStamp),tz=pytz.timezone(timeZoneId)).utctimetuple()))
    print retval
    return retval

# get to the day boundary and add the timezone offset.
def getTime(timeStamp,tzOffset):
    dt = datetime.datetime.fromtimestamp(float(timeStamp))
    dt1 = datetime.datetime(*dt.timetuple()[:3])
    return int(dt1.strftime("%s")) - tzOffset

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

@app.route("/spectrumbrowser/getDailyMaxMinMeanStats/<sensorId>/<minDate>/<maxDate>/<sessionId>", methods=["POST"])
def getDailyStatistics(sensorId, minDate, maxDate, sessionId):
    if not checkSessionId(sessionId):
        abort(404)
    tzOffset = int(request.args.get("tz","0"))
    tmin = getTime(minDate,tzOffset)
    tmax = getTime(maxDate,tzOffset)
    print "tmin " , tmin, "tmax ", tmax
    ndays = (tmax - tmin)/SECONDS_PER_DAY
    result = {}
    for day in range(0,ndays):
        tstart = tmin +  day*SECONDS_PER_DAY
        tend = tstart + SECONDS_PER_DAY
        queryString = { "sensorID" : sensorId, "t" : {'$gte':tstart,'$lte': tend}}
        cur = db.dataMessages.find(queryString)
        cur.batch_size(20)
        dailyStat = computeDailyMaxMinMeanStats(cur)
        result[day] = dailyStat
    return jsonify(result)

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



@app.route("/spectrumbrowser/getDataSummary/<sensorId>/<locationMessageId>/<sessionId>", methods=["POST"])
def getSensorDataDescriptions(sensorId,locationMessageId,sessionId):
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
    if tmin == '' and tmax == '':
        query = { "sensorID": sensorId, "locationMessageId":locationMessageId }
    elif tmin != ''  and tmax == '' :
        tzoffset = int(request.args.get("tz","0"))
        mintime = getTime(tmin,tzoffset)
        query = { "sensorID":sensorId, "locationMessageId":locationMessageId, "t" : {'$gte':mintime} }
    elif tmin == '' and tmax != '':
        tzoffset = int(request.args.get("tz","0"))
        maxtime = getTimeStamp(tmax,tzoffset)
        query = { "sensorID":sensorId, "locationMessageId":locationMessageId, "t" : {'$lte':maxtime} }
    else:
        tzoffset = int(request.args.get("tz","0"))
        mintime = getTime(tmin,tzoffset)
        maxtime = getTime(tmax,tzoffset)
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
            tStartDayBoundary = msg["tStartDayBoundaryTimeStamp"]
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
    tEndDayBoundary = endDayBoundary = lastMessage["tStartDayBoundaryTimeStamp"]
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
    tzoffset = int(request.args.get("tz","0"))
    mintime = getTime(startTime,tzoffset)
    maxtime = mintime + SECONDS_PER_DAY
    query = { "sensorID": sensorId,  "t": { '$lte':maxtime, '$gte':mintime}  }
    debugPrint(query)
    cur = db.dataMessages.find(query)
    if cur == None:
        abort(404)
    res = {}
    for msg in cur:
        res[msg["t"]-mintime] = {"t": msg["t"], \
                        "maxOccupancy":msg["maxOccupancy"],\
                        "minOccupancy":msg["minOccupancy"],\
                        "meanOccupancy":msg["meanOccupancy"],\
                        "medianOccupancy":msg["medianOccupancy"]}
    return jsonify(res)

@app.route("/spectrumbrowser/generateSingleAcquisitionSpectrogram/<sensorId>/<startTime>/<sessionId>", methods=["POST"])
def generateOneAcquisitionSpectrogram(sensorId,startTime,sessionId):
    if not checkSessionId(sessionId):
        abort(404)
    startTimeInt = int(startTime)
    query = { "sensorID": sensorId,  "t": startTimeInt  }
    debugPrint(query)
    msg = db.dataMessages.find_one(query)
    if msg == None:
        debugPrint("Data message not found for " + startTime)
        abort(404)
    if msg["mType"] != "FFT-Power":
        debugPrint("Operation not supported for " + msg["mType"])
        abort(400)
    fs = gridfs.GridFS(db,msg["sensorID"] + "/data")
    messageBytes = fs.get(ObjectId(msg["dataKey"])).read()
    debugPrint("Read " + str(len(messageBytes)))
    cutoff = int(request.args.get("cutoff",msg['noiseFloor'] + 2))
    iwidth = 800
    iheight = 402
    image_width = int(request.args.get("iwidth",iwidth))
    image_height = int(request.args.get("iheight",iheight))
    nM = msg["nM"]
    n = msg["mPar"]["n"]
    locationMessage = db.locationMessages.find_one({"_id":ObjectId(msg["locationMessageId"])})
    powerVal = np.array(np.zeros(n*nM))
    lengthToRead = n*nM
    occupancyCount = 0
    for i in range(0,lengthToRead):
        powerVal[i] = struct.unpack('b',messageBytes[i:i+1])[0]
        if powerVal[i] >= cutoff :
            occupancyCount += 1
    occupancy = float(occupancyCount) / float(n*nM)
    spectrogramData = powerVal.reshape(nM,n)
    frame1 = plt.gca()
    frame1.axes.get_xaxis().set_visible(False)
    frame1.axes.get_yaxis().set_visible(False)
    minpower = np.min(powerVal)
    maxpower = np.max(powerVal)
    cmap = plt.cm.spectral
    cmap.set_under(UNDER_CUTOFF_COLOR)
    cmap.set_over('black')
    #aspect=float(image_height)/float(image_width)
    dirname = "static/generated/" + sessionId
    if not os.path.exists(dirname):
        os.makedirs("static/generated/" + sessionId)
    fig = plt.imshow(spectrogramData,interpolation='nearest', extent=[0,image_width,0,image_height], \
        aspect="auto",vmin=cutoff,vmax=maxpower,cmap=cmap)
    spectrogramFile =  sessionId + "/" +sensorId + "." + str(startTime) + "." + str(cutoff)
    spectrogramFilePath = "static/generated/" + spectrogramFile
    plt.savefig(spectrogramFilePath + '.png', bbox_inches='tight', pad_inches=0, dpi=50)
    plt.close('all')
    norm = mpl.colors.Normalize(vmin=msg['noiseFloor'], vmax=maxpower)
    fig = plt.figure(figsize=(4,10))
    ax1 = fig.add_axes([0.0, 0, 0.1, 1])
    cb1 = mpl.colorbar.ColorbarBase(ax1, cmap=cmap, norm=norm, orientation='vertical')
    plt.savefig(spectrogramFilePath + '.cbar.png', bbox_inches='tight', pad_inches=0, dpi=50)
    plt.close('all')
    result = {"spectrogram":spectrogramFile+".png",     \
            "cbar":spectrogramFile+".cbar.png",         \
            "maxPower":maxpower,                        \
            "minPower":minpower,                        \
            "tStartLocalTime": msg["localTime"],        \
            "timeZone" : locationMessage["localTimeTzName"],   \
            "maxFreq":msg["mPar"]["fStart"],            \
            "minFreq":msg["mPar"]["fStop"],             \
            "timeDelta":msg["mPar"]["td"],              \
            "image_width":image_width,                  \
            "image_height": image_height}
    # see if it is well formed.
    debugPrint(result)
    return jsonify(result)






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
    app.run(debug="True")

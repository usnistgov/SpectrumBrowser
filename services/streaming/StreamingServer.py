#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
'''
Created on Jun 8, 2015

@author: local
'''

import Bootstrap
Bootstrap.setPath()
import signal
import Config
import util
import argparse
import socket
import DataStreamSharedState
from DataStreamSharedState import MemCache
import os
import traceback
import sys
import struct
from io import BytesIO
import binascii
from bson.json_util import dumps
import authentication
import json
import time
from Queue import Queue
import populate_db
import numpy as np
import ssl
import errno
from Defines import SYS
from Defines import LOC
from Defines import DATA
from Defines import TYPE
from Defines import SENSOR_ID
from Defines import SENSOR_KEY
from Defines import SPECTRUMS_PER_FRAME
from Defines import STREAMING_FILTER
from Defines import SYS_TO_DETECT
from Defines import DISABLED
from Defines import ADMIN
from Defines import USER
from Defines import STATUS
from Defines import OK
from Defines import NOK
from Defines import ERROR_MESSAGE
import SensorDb
import DataMessage
import CaptureDb
import DbCollections
from multiprocessing import Process
import Log
import logging
import pwd
from flask import Flask, request, abort,jsonify
from gevent import pywsgi
import Bootstrap
sbHome = Bootstrap.getSpectrumBrowserHome()

import sys
sys.path.append(sbHome + "/services/common")

WAITING_FOR_NEXT_INTERVAL = 1
BUFFERING = 2
POSTING = 3

app = Flask(__name__, static_url_path="")
app.static_folder = sbHome + "/flask/static"
app.template_folder = sbHome + "/flask/templates"
gwtSymbolMap = {}

lastDataMessage = {}
lastDataMessageInsertedAt = {}
lastDataMessageReceivedAt = {}
lastDataMessageOriginalTimeStamp = {}
childPids = []
bbuf = None
mySensorId = None
global sensorCommandDispatcherPid
sensorCommandDispatcherPid = None


memCache = None

checkForDataRate = True

class MyByteBuffer:

    def __init__(self, ws):
        self.ws = ws
        self.queue = Queue()
        self.buf = BytesIO()

    # TODO -- delete this - we dont stream from websockets any longer
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

    def close(self):
        self.buf.close()

# Socket IO for reading from sensor. 
def  startSocketServer(sock, streamingPort):
        global childPids
        while True:
            util.debugPrint("Starting sock server on " + str(streamingPort))
            try:
                (conn, addr) = sock.accept()
                util.debugPrint("startSocketServer Accepted a connection from " + str(addr))
                if Config.isSecure():
                    try :
                        cert = Config.getCertFile()
                        keyFile = Config.getKeyFile()
                        c = ssl.wrap_socket(conn,server_side = True, certfile = cert, keyfile=keyFile, ssl_version=ssl.PROTOCOL_SSLv3  )
                        t = Process(target=workerProc,args=(c,))
                        t.start()
                        pid = t.pid
                        util.debugPrint("startSocketServer: childpid " + str(pid))
                        childPids.append(pid)
                    except:
                        traceback.print_exc()
                        conn.close()
                        util.debugPrint("DataStreaming: Unexpected error")
                        continue
                else:
                    t = Process(target=workerProc, args=(conn,))
                    t.start()
                    pid = t.pid
                    childPids.append(pid)
            except socket.error as (code, msg):
                if code == errno.EINTR:
                    print "Trapped interrupted system call"
                    if "conn" in locals():
                        conn.close()
                    continue
                else:
                    raise



class BBuf():
    def __init__(self, conn):
        self.conn = conn
        self.buf = BytesIO()

    def read(self):
        try:
            val = self.buf.read(1)
            if val == "" or val == None :
                data = self.conn.recv(64)
                # max queue size - put this in config
                self.buf = BytesIO(data)
                val = self.buf.read(1)
            return val
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            raise

    def close(self):
	try:
           self.buf.close()
	except:
	   pass
	try:
           self.conn.shutdown(socket.SHUT_RDWR)
	except:
	   pass
	try:
           self.conn.close()
	except:
	   pass



    def readChar(self):
        val = self.read()
        return val

    def readByte(self):
        val = self.read()
        if val != None and val != "":
            retval = struct.unpack(">b", val)[0]
            return retval
        else:
            raise Exception("Read null value - client disconnected.")

def sendCommandToSensor(sensorId,command):
	DataStreamSharedState.sendCommandToSensor(sensorId,command)
    
def runSensorCommandDispatchWorker(conn,sensorId):
    soc = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    global memCache
    memCache = MemCache()
    port = memCache.getSensorArmPort(sensorId)
    soc.bind(("localhost",port))
    util.debugPrint("runSensorCommandDispatchWorker : port = " + str(port))
    try:
        while True:
    		command,addr  = soc.recvfrom(1024)
		if command == None or command == "":
                   break;
		util.debugPrint("runSensorArmWorker: got something ")
		util.debugPrint("runSensorArmWorker: got a message " + str(command))
    		conn.send(command.encode())
		commandJson = json.loads(command)
		if commandJson['command'] == 'retune' or commandJson['command'] == 'exit':
                   break;
    finally:
	util.debugPrint("runSensorCommandDispatchWorker: closing socket")
	soc.close()
	time.sleep(1)
	conn.close()
	os._exit(0)


def workerProc(conn):
    global bbuf
    global memCache
    if memCache == None :
        memCache = MemCache()
    bbuf = BBuf(conn)
    readFromInput(bbuf,conn)

def dataStream(ws):
    """
    Handle the data stream from a sensor.
    """
    print "Got a connection"
    bbuf = MyByteBuffer(ws)
    global memCache
    if memCache == None :
        memCache = MemCache()
    readFromInput(bbuf, True)


def signal_handler2(signo, frame):
     if sensorCommandDispatcherPid != None:
	print "signal_handler2 "
     	os.kill(sensorCommandDispatcherPid, signal.SIGKILL)
	

def readFromInput(bbuf,conn):
    util.debugPrint("DataStreaming:readFromInput")
    soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sensorCommandDispatcherPid = None
    memCache = MemCache()
    try:
        while True:
            lengthString = ""
            while True:
                lastChar = bbuf.readChar()
                if lastChar == None:
                    time.sleep(0.1)
                    return
                if len(lengthString) > 1000:
                    raise Exception("Formatting error")
                if lastChar == '{':
                    headerLength = int(lengthString.rstrip())
                    break
                else:
                    lengthString += str(lastChar)
            jsonStringBytes = "{"
            while len(jsonStringBytes) < headerLength:
                    jsonStringBytes += str(bbuf.readChar())

            jsonData = json.loads(jsonStringBytes)

            if not TYPE in jsonData or not SENSOR_ID in jsonData or not SENSOR_KEY in jsonData:
                util.errorPrint("Sensor Data Stream : Missing a required field")
                util.errorPrint("Invalid message -- closing connection : " + json.dumps(jsonData, indent=4))
                raise Exception("Invalid message")
                return


            sensorId = jsonData[SENSOR_ID]
            global mySensorId
            if mySensorId == None:
                mySensorId = sensorId
            elif mySensorId != sensorId:
                raise Exception("Sensor ID mismatch " + mySensorId + " / " + sensorId)

            sensorKey = jsonData[SENSOR_KEY]
            if not authentication.authenticateSensor(sensorId, sensorKey):
                util.errorPrint("Sensor authentication failed: " + sensorId)
                raise Exception("Authentication failure")
                return

            if memCache.getStreamingServerPid(sensorId) == -1 :
                memCache.setStreamingServerPid(sensorId)
            elif memCache.getStreamingServerPid(sensorId) != os.getpid() :
                util.errorPrint("Handling connection for this sensor already ")
		try:
		   os.kill(memcache.getStreamingServerPid(sensorId),0)
                   raise Exception("Sensor already connected PID = " + str(memCache.getStreamingServerPid(sensorId)))
                   return
	        except:
                   util.debugPrint("Process not found. ")

            util.debugPrint("DataStreaming: Message = " + dumps(jsonData, sort_keys=True, indent=4))

            sensorObj = SensorDb.getSensorObj(sensorId)
            if not sensorObj.isStreamingEnabled() or sensorObj.getStreamingParameters() == None:
                raise Exception("Streaming is not enabled")
                return



            # the last time a data message was inserted
            if jsonData[TYPE] == DATA:
                util.debugPrint("pubsubPort : " + str(memCache.getPubSubPort(sensorId)))
                if not "Sys2Detect" in jsonData:
                    jsonData[SYS_TO_DETECT] = "LTE"
                DataMessage.init(jsonData)
    	        t = Process(target=runSensorCommandDispatchWorker, args=(conn,sensorId))
	        t.start()
	        sensorCommandDispatcherPid = t.pid
		childPids.append(sensorCommandDispatcherPid)
                cutoff = DataMessage.getThreshold(jsonData)
                n = DataMessage.getNumberOfFrequencyBins(jsonData)
                sensorId = DataMessage.getSensorId(jsonData)
                lastDataMessageReceivedAt[sensorId] = time.time()
                lastDataMessageOriginalTimeStamp[sensorId] = DataMessage.getTime(jsonData)
                
                # Check if the measurement type reported by the sensor matches that in the sensordb
                measurementType = DataMessage.getMeasurementType(jsonData)
                if sensorObj.getMeasurementType() != measurementType:
                    raise Exception("Measurement type mismatch " + sensorObj.getMeasurementType() + \
                                    " / " + measurementType)

                # Check if the time per measurement reported by the sensor matches that in the sensordb
                timePerMeasurement = sensorObj.getStreamingSecondsPerFrame()
                util.debugPrint("StreamingServer: timePerMeasurement " + str(timePerMeasurement))
                if timePerMeasurement != DataMessage.getTimePerMeasurement(jsonData):
                   raise Exception("TimePerMeasurement mismatch " + str(timePerMeasurement) + "/" +\
                         str(DataMessage.getTimePerMeasurement(jsonData)))

                # The sampling interval for write to the database.
                streamingSamplingIntervalSeconds = sensorObj.getStreamingSamplingIntervalSeconds()
                
                # The number of measurements per capture
                measurementsPerCapture = int (streamingSamplingIntervalSeconds / timePerMeasurement)
                util.debugPrint("StreamingServer: measurementsPerCapture " + str(measurementsPerCapture))

                # The number of power value samples per capture.
                samplesPerCapture = int((streamingSamplingIntervalSeconds / timePerMeasurement) * n)

                # The number of spectrums per frame sent to the browser.
                spectrumsPerFrame = 1
                jsonData[SPECTRUMS_PER_FRAME] = spectrumsPerFrame
                
                # The streaming filter of the sensor (MAX_HOLD or AVG)
                jsonData[STREAMING_FILTER] = sensorObj.getStreamingFilter()

                # The band name sys2detect:minfreq:maxfreq string for the reported measurement.
                bandName = DataMessage.getFreqRange(jsonData)

                # Keep a copy of the last data message for periodic insertion into the db
                memCache.setLastDataMessage(sensorId, bandName, json.dumps(jsonData))
                # captureBufferCounter is a pointer into the capture buffer.
                captureBufferCounter = 0
                powerArrayCounter = 0
                timingCounter = 0

                # initialize the "prev occupancy array" 
                prevOccupancyArray = [-1 for i in range(0, n)]
                occupancyArray = [0 for i in range(0, n)]
                occupancyTimer = time.time()
                if not sensorId in lastDataMessage:
                    lastDataMessage[sensorId] = jsonData
                powerVal = [0 for i in range(0, n)]

                startTime = time.time()
                sensorObj = SensorDb.getSensorObj(sensorId)
                if sensorObj == None:
                        raise Exception("Sensor not found")
                if sensorObj.getSensorStatus() == DISABLED :
                        bbuf.close()
                        raise Exception("Sensor is disabled")
                if not sensorObj.isStreamingEnabled():
                        raise Exception("Streaming is disabled")
                isStreamingCaptureEnabled = sensorObj.isStreamingCaptureEnabled()
                if isStreamingCaptureEnabled:
                    sensorData = [0 for i in range(0, samplesPerCapture)]
                while True:
                        data = bbuf.readByte()
                        if isStreamingCaptureEnabled:
                            sensorData[captureBufferCounter] = data
                        powerVal[powerArrayCounter] = data
                        now = time.time()
                        if isStreamingCaptureEnabled and captureBufferCounter + 1 == samplesPerCapture:
                            # Buffer is full so push the data into mongod.
                            util.debugPrint("Inserting Data message")
                            captureBufferCounter = 0
                            # Time offset since the last data message was received.
                            timeOffset = time.time() - lastDataMessageReceivedAt[sensorId]
                            # Offset the capture by the time since the DataMessage header was received.
                            lastDataMessage[sensorId]["t"] = lastDataMessageOriginalTimeStamp[sensorId] + \
                                                                int(timeOffset)
                            lastDataMessage[sensorId]["nM"] = measurementsPerCapture
                            lastDataMessage[sensorId]["mPar"]["td"] = int(now - occupancyTimer)
                            lastDataMessage[sensorId]["mPar"]["tm"] = timePerMeasurement
                            headerStr = json.dumps(lastDataMessage[sensorId], indent=4)
                            util.debugPrint("StreamingServer: headerStr " + headerStr)
                            headerLength = len(headerStr)
                            if isStreamingCaptureEnabled:
                                # Start the db operation in a seperate process
                                p = Process(target=populate_db.put_data, \
                                                          args=(headerStr, headerLength), \
                                                kwargs={"filedesc":None, "powers":sensorData})
                                p.start()
                            lastDataMessageInsertedAt[sensorId] = time.time()
                            occupancyTimer = time.time()
                        else:
                            captureBufferCounter = captureBufferCounter + 1

                        if data > cutoff:
                            occupancyArray[powerArrayCounter] = 1
                        else:
                            occupancyArray[powerArrayCounter] = 0

                        # print "occupancyArray", occupancyArray
                        if (powerArrayCounter + 1) == n:
                            # Get the occupancy subscription counter.
                            if memCache.getSubscriptionCount(sensorId) != 0:
                                if not np.array_equal(occupancyArray , prevOccupancyArray):
				    port = memCache.getPubSubPort(sensorId)
                                    soc.sendto(json.dumps({sensorId:occupancyArray}),("localhost",port))
                                prevOccupancyArray = np.array(occupancyArray)

                            # sending data as CSV values to the browser
                            listenerCount = memCache.getStreamingListenerCount(sensorId)
                            if listenerCount > 0:
                                sensordata = str(powerVal)[1:-1].replace(" ", "")
                                memCache.setSensorData(sensorId, bandName, sensordata)
                            # Record the occupancy for the measurements.
                            # Allow for 10% jitter.
                            if timingCounter == 1000 and checkForDataRate:
                                if ((now - startTime) / 1000.0 < timePerMeasurement / 2 or (now - startTime) / 1000.0 > timePerMeasurement * 2) :
                                    print " delta ", now - startTime, "global counter ", powerArrayCounter
                                    util.errorPrint("Data coming in too fast or too slow - sensor configuration problem.")
                                    raise Exception("Data coming in too fast - sensor configuration problem.")
                                else:
                                    startTime = now
                            lastdataseen = now
                            if listenerCount > 0:
                                memCache.setLastDataSeenTimeStamp(sensorId, bandName, lastdataseen)
                            powerArrayCounter = 0
                        else:
                            powerArrayCounter = powerArrayCounter + 1
                        timingCounter = timingCounter + 1
            elif jsonData[TYPE] == SYS:
                util.debugPrint("DataStreaming: Got a System message -- adding to the database")
                populate_db.put_data(jsonStringBytes, headerLength)
            elif jsonData[TYPE] == LOC:
                util.debugPrint("DataStreaming: Got a Location Message -- adding to the database")
                populate_db.put_data(jsonStringBytes, headerLength)
    finally:
        util.debugPrint("Closing sockets for sensorId " + sensorId)
        memCache.removeStreamingServerPid(sensorId)
	port = memCache.getSensorArmPort(sensorId)
	sendCommandToSensor(sensorId,json.dumps({"sensorId":sensorId,"command":"exit"}))
	memCache.releaseSensorArmPort(sensorId)
        bbuf.close()
	time.sleep(1)
        soc.close()

	


def signal_handler(signo, frame):
        print('Caught signal! Exitting.')
        global mySensorId
        if mySensorId != None:
            memCache.removeStreamingServerPid(mySensorId)
	    memCache.releaseSensorArmPort(mySensorId)

        for pid in childPids:
            try:
                print "Killing : " , pid
                os.kill(pid, signal.SIGINT)
            except:
                print str(pid), "Not Found"
        if bbuf != None:
            bbuf.close()


def handleSIGCHLD(signo, frame):
    print("Caught SigChld")
    pid, exitcode = os.waitpid(-1, 0)
    print "Pid of dead child ", pid
    index = 0
    for p in childPids:
        if p == pid:
            childPids.pop(index)
        index = index + 1




def startStreamingServer(port):
    """
    Start the streaming server and accept connections.
    """
    global memCache
    if memCache == None :
        memCache = MemCache()
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    l_onoff = 1
    l_linger = 0
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,                                                                                                                     
                 struct.pack('ii', l_onoff, l_linger))
    portAssigned = False
    for p in range(port, port + 10, 2):
        try :
            print 'Trying port ', p
            soc.bind(('0.0.0.0', p))
            soc.listen(10)
            socketServerPort = p

            memCache.setSocketServerPort(p)
            portAssigned = True
            util.debugPrint("DataStreaming: Bound to port " + str(p))
            break
        except:
            print sys.exc_info()
            traceback.print_exc()
            util.debugPrint("DataStreaming: Bind failed - retry")
    if portAssigned:
        global occupancyQueue
        socketServer = startSocketServer(soc, socketServerPort)
        socketServer.start()
    else:
        util.errorPrint("DataStreaming: Streaming disabled on worker - no port found.")





@app.route("/sensorcontrol/armSensor/<sensorId>", methods=["POST"])
def armSensor(sensorId):
    """
    Arm the sensor for I/Q capture.

    URL Path:
	sensorId -- sensor ID.
	
    URL Args: None

    Request Body:
	
	- agentName : Name of the agent to arm/disarm sensor.
	- key       : Key (password) of the agent to arm/disarm the sensor.

    HTTP Return Codes:

	- 200 OK : invocation was successful.
        - 403 Forbidden : authentication failure
	- 400 Bad request : Sensor is not a streaming sensor.

    Example Invocation:

    ::

       params = {}
       params["agentName"] = "NIST_ESC"
       params["key"] = "ESC_PASS"
       r = requests.post("https://"+ host + ":" + str(443) + "/sensorcontrol/disarmSensor/" + self.sensorId,data=json.dumps(params),verify=False)

    ::

    """
    try:
        util.debugPrint("armSensor :  sensorId " + sensorId)
        requestStr = request.data
        accountData = json.loads(requestStr)
        if not authentication.authenticateSensorAgent(accountData):
                abort(403)
	sensorConfig = SensorDb.getSensorObj(sensorId)
	if sensorConfig == None:
		abort(404)
	if not sensorConfig.isStreamingEnabled() :
		abort(400)
	sendCommandToSensor(sensorId,json.dumps({"sensorId":sensorId,"command":"arm"}))
	return jsonify({STATUS:OK})
    except:
       print "Unexpected error:", sys.exc_info()[0]
       print sys.exc_info()
       traceback.print_exc()
       util.logStackTrace(sys.exc_info())
       raise

@app.route("/sensorcontrol/disarmSensor/<sensorId>", methods=["POST"])
def disarmSensor(sensorId):
    """
    Arm the sensor for I/Q capture.

    URL Path:
	sessionId -- the session ID of the login session.
	
    URL Args: None

    Request Body:

	- agentName : Name of the agent to arm/disarm sensor.
	- key   : password of the agent to arm/disarm the sensor.

    HTTP Return Codes:

	- 200 OK : invocation was successful.
        - 403 Forbidden : authentication failure
	- 400 Bad request : Sensor is not a streaming sensor.

    Example Invocation:

    ::

       params = {}
       params["agentName"] = "NIST_ESC"
       params["key"] = "ESC_PASS"
       r = requests.post("https://"+ host + ":" + str(443) + "/sensorcontrol/disarmSensor/" + self.sensorId,data=json.dumps(params),verify=False)

    ::

    """
    try:
        util.debugPrint("disarmSensor :  sensorId " + sensorId)
        requestStr = request.data
        accountData = json.loads(requestStr)
        if not authentication.authenticateSensorAgent(accountData):
                abort(403)
	sensorConfig = SensorDb.getSensorObj(sensorId)
	if sensorConfig == None:
		abort(404)
	if not sensorConfig.isStreamingEnabled() :
		abort(400)
	sendCommandToSensor(sensorId, json.dumps({"sensorId":sensorId,"command":"disarm"}))
	return jsonify({STATUS:OK})
    except:
       print "Unexpected error:", sys.exc_info()[0]
       print sys.exc_info()
       traceback.print_exc()
       util.logStackTrace(sys.exc_info())
       raise

@app.route("/sensorcontrol/retuneSensor/<sensorId>/<bandName>",methods=["POST"])
def retuneSensor(sensorId,bandName):
    """
    retune a sensor to a band. The bandName should correspond to a band that is suppored by the sensor.
    
    URL Path:
	sensorId -- the session ID of the login session.
	bandName -- the band name to tune the sensor to.
	
    URL Args: None

    Request Body:
    Contains authentication information for the agent that is authorized
    to arm and disarm the sensor:

	- agentName : Name of the agent to arm/disarm sensor.
	- key   : password of the agent to arm/disarm the sensor.

    HTTP Return Codes:

	- 200 OK : invocation was successful.
        - 403 Forbidden : authentication failure
	- 400 Bad request : Sensor is not a streaming sensor.

    Example Invocation:

    ::

       params = {}
       params["agentName"] = "NIST_ESC"
       params["key"] = "ESC_PASS"
       r = requests.post("https://"+ host + ":" + str(443) + "/sensorcontrol/retuneSensor/" + self.sensorId + "/LTE:70315780:713315880",data=json.dumps(params),verify=False)


    """
    try:
        util.debugPrint("retuneSensor : sensorId " + sensorId + " bandName " + bandName )
        requestStr = request.data
	if requestStr == None:
		abort(400)
        accountData = json.loads(requestStr)
        if not authentication.authenticateSensorAgent(accountData):
                abort(403)
	sensorConfig = SensorDb.getSensorObj(sensorId)
	if sensorConfig == None:
		abort(404)
	if not sensorConfig.isStreamingEnabled() :
		abort(400)
	band =  SensorDb.getBand(sensorId,bandName)
	retval = SensorDb.activateBand(sensorId,bandName)
	sendCommandToSensor(sensorId, json.dumps({"sensorId":sensorId,"command":"retune", "bandName":band}))
	return jsonify(retval)
    except:
       print "Unexpected error:", sys.exc_info()[0]
       print sys.exc_info()
       traceback.print_exc()
       util.logStackTrace(sys.exc_info())
       raise

@app.route("/sensorcontrol/disconnectSensor/<sensorId>",methods=["POST"])
def disconnectSensor(sensorId):
    """
    Send a sensor a command to exit.
    
    URL Path:
	sensorId -- the session ID of the login session.
	
    URL Args: None

    Request Body:
    Contains authentication information for the agent that is authorized
    to arm and disarm the sensor:

	- agentName : Name of the agent to arm/disarm sensor.
	- key   : password of the agent to arm/disarm the sensor.

    HTTP Return Codes:

	- 200 OK : invocation was successful.
        - 403 Forbidden : authentication failure
	- 400 Bad request : Sensor is not a streaming sensor.

    Example Invocation:

    ::

       params = {}
       params["agentName"] = "NIST_ESC"
       params["key"] = "ESC_PASS"
       r = requests.post("https://"+ host + ":" + str(443) + "/sensorcontrol/disconnectSensor/" + self.sensorId + "/LTE:70315780:713315880",data=json.dumps(params),verify=False)


    """
    try:
        util.debugPrint("disconnectSensor : sensorId " + sensorId )
        requestStr = request.data
	if requestStr == None:
		abort(400)
        accountData = json.loads(requestStr)
        if not authentication.authenticateSensorAgent(accountData):
                abort(403)
	sensorConfig = SensorDb.getSensorObj(sensorId)
	if sensorConfig == None:
		abort(404)
	if not sensorConfig.isStreamingEnabled() :
		abort(400)
	sendCommandToSensor(sensorId,json.dumps({"sensorId":sensorId,"command":"exit"}))
	return jsonify({STATUS:OK})
    except:
       print "Unexpected error:", sys.exc_info()[0]
       print sys.exc_info()
       traceback.print_exc()
       util.logStackTrace(sys.exc_info())
       raise

@app.route("/sensorcontrol/runForensics/<sensorId>/<algorithm>/<timestamp>/<sessionId>",methods=["POST"])
def runForensics(sensorId,algorithm,timestamp,sessionId):
    """
    Run forensics at the sensor. This just relays the command to the sensor. The sensor will post back
    after the processing is done. 

    timestamp -- the timestamp of the capture.
    algorithm -- the algortithm  to appy (from the toolbox that lives on the sensor)
    sessionId -- the login session id.

    """
    try:
        if not authentication.checkSessionId(sessionId,USER):
	   util.debugPrint("runForensics - request body not found")
	   abort(403)
	command = {"sensorId":sensorId, "timestamp":int(timestamp),"algorithm":algorithm,"command":"analyze"}
	sendCommandToSensor(sensorId,json.dumps(command))
	return jsonify({STATUS:OK})
    except:
       print "Unexpected error:", sys.exc_info()[0]
       print sys.exc_info()
       traceback.print_exc()
       util.logStackTrace(sys.exc_info())
       raise
	



@app.route("/eventstream/postCaptureEvent",methods=["POST"])
def postCaptureEvent():
    """
    Handle post of a capture event from a sensor 

    URL Path:
	
        - None

    URL Parameters:
   
        - None

    Request Body:

        - CaptureEvent JSON structure which includes the sensor ID and sensor key. 
          These are used for verifying the request. See MSOD specification for definition of 
          CaptureEvent structure.


    HTTP Return Codes:

       - 200 OK. A JSON Document containing {"status":"OK"} is returned.
    
    """
    try:
        requestStr = request.data
	if requestStr == None:
	   util.debugPrint("postCaptureEvent - request body not found")
	   abort(400)
	
	util.debugPrint("postCaptureEvent " + requestStr)
        captureEvent = json.loads(requestStr)

	if not SENSOR_ID in captureEvent or SENSOR_KEY not in captureEvent:
	   util.debugPrint("postCaptureEvent - missing a required field")
	   abort(400)
	
	sensorId = captureEvent[SENSOR_ID]
	sensorConfig = SensorDb.getSensorObj(sensorId)
	if sensorConfig == None:
	        util.debugPrint("postCaptureEvent - sensor not found")
		abort(404)
	sensorKey = captureEvent[SENSOR_KEY]
	if not authentication.authenticateSensor(sensorId,sensorKey):
		abort(403)
	return jsonify(CaptureDb.insertEvent(sensorId,captureEvent))
    except:
       print "Unexpected error:", sys.exc_info()[0]
       print sys.exc_info()
       traceback.print_exc()
       util.logStackTrace(sys.exc_info())
       raise

@app.route("/eventstream/getCaptureEvents/<sensorId>/<startDate>/<dayCount>/<sessionId>",methods=["POST"])
def getCaptureEvents(sensorId,startDate,dayCount,sessionId):
    """
    get the capture events for a given sensor within the specified date range.


    """
    try:
        if not authentication.checkSessionId(sessionId,USER):
	      util.debugPrint("getCaptureEvents : failed authentication")
	      abort(403)
        try: 
	     sdate = int(startDate)
	     dcount = int(dayCount)
    	except ValueError: 
		abort(400)
	if sdate < 0 or dcount < 0:
		abort(400)
	elif dcount == 0:
	       abort(400)
	return jsonify(CaptureDb.getEvents(sensorId,sdate,dcount))
    except:
       print "Unexpected error:", sys.exc_info()[0]
       print sys.exc_info()
       traceback.print_exc()
       util.logStackTrace(sys.exc_info())
       raise

@app.route("/eventstream/deleteCaptureEvents/<sensorId>/<startDate>/<sessionId>",methods=["POST"])
def deleteCaptureEvents(sensorId,startDate,sessionId):
    """
    Delete the events from the capture db. 
    Send a message to the sensor to do the same.
    """
    try:
        if not authentication.checkSessionId(sessionId,ADMIN):
	      util.debugPrint("deleteCaptureEvents : failed authentication")
	      abort(403)
	sdate = int(startDate)
	if sdate < 0:
           util.debugPrint("deleteCaptureEvents : illegal param")
           abort(400)
        else:
           CaptureDb.deleteCaptureDb(sensorId,sdate)
    	   global memCache
    	   if memCache == None :
        	  memCache = MemCache()
	   command = json.dumps({"sensorId":sensorId, "timestamp":sdate,"command":"garbage_collect"})
	   sendCommandToSensor(sensorId,command)
	   return jsonify({STATUS:"OK"})
    except:
       print "Unexpected error:", sys.exc_info()[0]
       print sys.exc_info()
       traceback.print_exc()
       util.logStackTrace(sys.exc_info())
       raise

@app.route("/eventstream/postForensics/<sensorId>",methods=["POST"])
def postForensics(sensorId):
    try:
       requestStr = request.data
       requestJson = json.loads(requestStr)
       if not authentication.authenticateSensor(sensorId,requestJson[SENSOR_KEY]):
          abort(403)
       t = requestJson['t']
       captureEvent = CaptureDb.getEvent(sensorId,t)
       if captureEvent != None:
       	   lastId = captureEvent["_id"]
           del captureEvent["_id"]
	   captureEvent["forensicsReport"] = requestJson["forensicsReport"]
           return  jsonify(CaptureDb.updateEvent(lastId,captureEvent))
       else:
           return jsonify({ STATUS: NOK, ERROR_MESSAGE: "Event not found" })
    except:
       print "Unexpected error:", sys.exc_info()[0]
       print sys.exc_info()
       traceback.print_exc()
       util.logStackTrace(sys.exc_info())
       raise
        
        


def startWsgiServer():
    util.debugPrint("Starting WSGI server")    
    server = pywsgi.WSGIServer(('localhost', 8004), app)
    server.serve_forever()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGCHLD, handleSIGCHLD)
    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument("--pidfile", help="PID file", default=".streaming.pid")
    parser.add_argument("--logfile", help="LOG file", default="/tmp/streaming.log")
    parser.add_argument("--username", help="USER name", default="spectrumbrowser")
    parser.add_argument("--groupname", help="GROUP name", default="spectrumbrowser")
    parser.add_argument("--port", help="Streaming Server Port", default="9000")
    parser.add_argument("--daemon", help="daemon flag", default="True")

    args = parser.parse_args()
    isDaemon  = args.daemon == "True"
    port = int(args.port)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(args.logfile)
    logger.addHandler(fh)

    util.debugPrint(">>>>> Starting Streaming Server <<<<< ")

    t = Process(target=startWsgiServer)
    t.start()

    if isDaemon:
	import daemon
	import daemon.pidfile
        context = daemon.DaemonContext()
        context.stdin = sys.stdin
        context.stderr = open(args.logfile,'a')
        context.stdout = open(args.logfile,'a')
        context.files_preserve = [fh.stream]
        context.uid = pwd.getpwnam(args.username).pw_uid
        context.gid = pwd.getpwnam(args.groupname).pw_gid
        app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
        app.config['CORS_HEADERS'] = 'Content-Type'
        Log.loadGwtSymbolMap()
 	# There is a race condition here but it will do for us.
        if os.path.exists(args.pidfile):
            pid = open(args.pidfile).read()
            try :
                os.kill(int(pid), 0)
                print "svc is running -- not starting"
                sys.exit(-1)
                os._exit(-1)
            except:
                print "removing pidfile and starting"
                os.remove(args.pidfile)
        context.pidfile = daemon.pidfile.TimeoutPIDLockFile(args.pidfile)
        with context:
            print "Starting streaming server"
            startStreamingServer(port)
    else:
        with util.pidfile(args.pidfile):
            startStreamingServer(port)







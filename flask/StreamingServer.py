'''
Created on Jun 8, 2015

@author: local
'''

import signal
import Config
import util
import argparse
import socket
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
import SensorDb
import DataMessage
from multiprocessing import Process
import zmq
#from prctl import prctl

WAITING_FOR_NEXT_INTERVAL = 1
BUFFERING = 2
POSTING = 3


lastDataMessage={}
lastDataMessageInsertedAt={}
lastDataMessageReceivedAt={}
lastDataMessageOriginalTimeStamp={}
childPids = []
bbuf = None


memCache = None

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

# Socket IO for reading from sensor. TODO : make this a secure socket.
def  startSocketServer(sock,streamingPort):
        global childPids
        while True:
            util.debugPrint("Starting sock server on "+ str(streamingPort))
            try:
                (conn,addr) = sock.accept()
                if Config.isSecure():
                    try :
                        cert = Config.getCertFile()
                        c = ssl.wrap_socket(conn,server_side = True, certfile = cert, ssl_version=ssl.PROTOCOL_SSLv3  )
                        t = Process(target=workerProc,args=(c,))
                        t.start()
                        pid = t.pid
                        print "childpid ",pid
                        childPids.append(pid)
                    except:
                        traceback.print_exc()
                        conn.close()
                        util.debugPrint( "DataStreaming: Unexpected error")
                        continue
                else:
                    t = Process(target=workerProc,args=(conn,))
                    util.debugPrint("startSocketServer Accepted a connection from "+str(addr))
                    t.start()
                    pid = t.pid
                    childPids.append(pid)
            except socket.error as (code,msg):
                if code == errno.EINTR:
                    print "Trapped interrupted system call"
                    conn.close()
                    continue
                else:
                    raise



class BBuf():
    def __init__(self,conn):
        self.conn = conn
        self.buf = BytesIO()

    def read(self):
        try:
            val = self.buf.read(1)
            if val == "" or val == None :
                data = self.conn.recv(64)
                #max queue size - put this in config
                self.buf = BytesIO(data)
                val =  self.buf.read(1)
            return val
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            raise

    def close(self):
        self.buf.close()
        self.conn.shutdown(socket.SHUT_RDWR)
        self.conn.close()



    def readChar(self):
        val = self.read()
        return val

    def readByte(self):
        val = self.read()
        try:
            if val != None:
                retval = struct.unpack(">b", val)[0]
                return retval
            else:
                return None
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            print "val = ", str(val)
            raise

def workerProc(conn):
    global memCache
    global bbuf
    #prctl(1, signal.SIGHUP)
    if memCache == None :
        memCache = MemCache()
    bbuf = BBuf(conn)
    readFromInput(bbuf)

def dataStream(ws):
    """
    Handle the data stream from a sensor.
    """
    print "Got a connection"
    bbuf = MyByteBuffer(ws)
    global memCache
    if memCache == None :
        memCache = MemCache()
    readFromInput(bbuf,True)


def readFromInput(bbuf):
    util.debugPrint("DataStreaming:readFromInput")
    context = zmq.Context()
    soc = context.socket(zmq.PUB)
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
                util.errorPrint("Invalid message -- closing connection : " + json.dumps(jsonData,indent=4))
                raise Exception("Invalid message")
                return
            sensorId = jsonData[SENSOR_ID]
            sensorKey = jsonData[SENSOR_KEY]
            if not authentication.authenticateSensor(sensorId, sensorKey):
                util.errorPrint("Sensor authentication failed: " + sensorId)
                raise Exception("Authentication failure")
                return

            util.debugPrint( "DataStreaming: Message = " + dumps(jsonData, sort_keys=True, indent=4))

            sensorObj = SensorDb.getSensorObj(sensorId)
            if not sensorObj.isStreamingEnabled():
                raise Exception("Streaming is not enabled")
                return
            # the last time a data message was inserted
            if jsonData[TYPE] == DATA:
                util.debugPrint( "pubsubPort : " + str(memCache.getPubSubPort(sensorId)))
                soc.bind("tcp://*:" + str(memCache.getPubSubPort(sensorId)))
                #BUGBUG -- remove this.
                if not "Sys2Detect" in jsonData:
                    jsonData[SYS_TO_DETECT] = "LTE"
                DataMessage.init(jsonData)
                cutoff = DataMessage.getThreshold(jsonData)
                n = DataMessage.getNumberOfFrequencyBins(jsonData)
                sensorId = DataMessage.getSensorId(jsonData)
                lastDataMessageReceivedAt[sensorId] = time.time()
                lastDataMessageOriginalTimeStamp[sensorId] = DataMessage.getTime(jsonData)
                measurementType = DataMessage.getMeasurementType(jsonData)
                if sensorObj.getMeasurementType() != measurementType:
                    raise Exception("Measurement type mismatch " + sensorObj.getMeasurementType() + \
                                    " / " + measurementType )
                timePerMeasurement = sensorObj.getStreamingSecondsPerFrame()
                measurementsPerCapture = int (sensorObj.getStreamingSamplingIntervalSeconds()/ timePerMeasurement)
                samplesPerCapture = int((sensorObj.getStreamingSamplingIntervalSeconds()/ timePerMeasurement)*n)
                sensorData = [0 for i in range(0,samplesPerCapture)]
                spectrumsPerFrame = 1
                jsonData[SPECTRUMS_PER_FRAME] = spectrumsPerFrame
                jsonData[STREAMING_FILTER] = sensorObj.getStreamingFilter()
                bandName = DataMessage.getFreqRange(jsonData)
                # Keep a copy of the last data message for periodic insertion into the db
                memCache.setLastDataMessage(sensorId,bandName,json.dumps(jsonData))
                # Buffer counter is a pointer into the capture buffer.
                bufferCounter = 0
                # globalCounter is a running global byte counter of the
                # received data (TODO -- Could make this a modulo n counter)
                globalCounter = 0
                prevOccupancyArray = [-1 for i in range(0,n)]
                occupancyArray = [0 for i in range(0,n)]
                occupancyTimer = time.time()
                if not sensorId in lastDataMessage:
                    lastDataMessage[sensorId] = jsonData
                powerVal = [0 for i in range(0,n)]

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
                while True:
                        data = bbuf.readByte()
                        if isStreamingCaptureEnabled:
                            sensorData[bufferCounter] = data
                        powerVal[globalCounter % n] = data
                        now = time.time()
                        if isStreamingCaptureEnabled and bufferCounter + 1 == samplesPerCapture:
                            # Buffer is full so push the data into mongod.
                            util.debugPrint("Inserting Data message")
                            bufferCounter = 0
                            # Time offset since the last data message was received.
                            timeOffset = time.time() - lastDataMessageReceivedAt[sensorId]
                            # Offset the capture by the time since the DataMessage header was received.
                            lastDataMessage[sensorId]["t"] = lastDataMessageOriginalTimeStamp[sensorId] +\
                                                                int(timeOffset)
                            lastDataMessage[sensorId]["nM"] = measurementsPerCapture
                            lastDataMessage[sensorId]["mPar"]["td"] = int(now - occupancyTimer)
                            lastDataMessage[sensorId]["mPar"]["tm"] = timePerMeasurement
                            headerStr = json.dumps(lastDataMessage[sensorId],indent=4)
                            headerLength = len(headerStr)
                            if isStreamingCaptureEnabled:
                                # Start the db operation in a seperate process
                                p = Process(target=populate_db.put_data, \
                                                          args=(headerStr,headerLength),\
                                                kwargs={"filedesc":None,"powers":sensorData})
                                p.start()
                            lastDataMessageInsertedAt[sensorId] = time.time()
                            occupancyTimer = time.time()
                        if data > cutoff:
                            occupancyArray[globalCounter%n] = 1
                        else:
                            occupancyArray[globalCounter %n] = 0
                        #print "occupancyArray", occupancyArray
                        if (globalCounter + 1) %n == 0 :
                            # Get the occupancy subscription counter.
                            if memCache.getSubscriptionCount(sensorId) != 0:
                                if not np.array_equal(occupancyArray ,prevOccupancyArray):
                                    soc.send_pyobj({sensorId:occupancyArray})
                                prevOccupancyArray = np.array(occupancyArray)
                            # sending data as CSV values to the browser
                            listenerCount = memCache.getStreamingListenerCount(sensorId)
                            if listenerCount > 0:
                                sensordata = str(powerVal)[1:-1].replace(" ", "")
                                memCache.setSensorData(sensorId,bandName,sensordata)
                            # Record the occupancy for the measurements.
                            # Allow for 10% jitter.
                            if now - startTime < timePerMeasurement/2 or now - startTime > timePerMeasurement*2 :
                                print " delta ", now - startTime, "global counter ", globalCounter
                                util.errorPrint("Data coming in too fast - sensor configuration problem.")
                                raise Exception("Data coming in too fast - sensor configuration problem.")
                            else:
                                startTime = now
                            lastdataseen  = now
                            if listenerCount >0:
                                memCache.setLastDataSeenTimeStamp(sensorId,bandName,lastdataseen)
                        globalCounter = globalCounter + 1
                        bufferCounter = bufferCounter + 1
            elif jsonData[TYPE] == SYS:
                util.debugPrint("DataStreaming: Got a System message -- adding to the database")
                populate_db.put_data(jsonStringBytes, headerLength)
                memCache.setStreamingServerPid(sensorId)
            elif jsonData[TYPE] == LOC:
                util.debugPrint("DataStreaming: Got a Location Message -- adding to the database")
                populate_db.put_data(jsonStringBytes, headerLength)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()

        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
    finally:
        print "Closing pub socket"
        bbuf.close()
        soc.close()



def signal_handler(signo, frame):
        print('Caught signal! Exitting.')
        for pid in childPids:
            try:
                print "Killing : " ,pid
                os.kill(pid,signal.SIGINT)
            except:
                print str(pid),"Not Found"
        if bbuf != None:
            bbuf.close()
        os._exit(0)


def handleSIGCHLD(signo,frame):
    print("Caught SigChld")
    pid,exitcode = os.waitpid(-1, 0)
    print "Pid of dead child ",pid
    index = 0
    for p in childPids:
        if p == pid:
            childPids.pop(index)
        index = index+1



def startStreamingServer():
    # The following code fragment is executed when the module is loaded.
    global memCache

    if memCache == None :
        memCache = MemCache()
    #prctl(1, signal.SIGHUP)
    port = Config.getStreamingServerPort()
    soc = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    portAssigned = False
    for p in range(port,port+10,2):
        try :
            print 'Trying port ',p
            soc.bind(('0.0.0.0',p))
            soc.listen(10)
            socketServerPort = p

            memCache.setSocketServerPort(p)
            portAssigned = True
            util.debugPrint( "DataStreaming: Bound to port "+ str(p))
            break
        except:
            print sys.exc_info()
            traceback.print_exc()
            util.debugPrint( "DataStreaming: Bind failed - retry")
    if portAssigned:
        global occupancyQueue
        socketServer = startSocketServer(soc,socketServerPort)
        socketServer.start()
    else:
        util.errorPrint( "DataStreaming: Streaming disabled on worker - no port found.")


if __name__ == '__main__':
    signal.signal(signal.SIGINT,signal_handler)
    signal.signal(signal.SIGHUP,signal_handler)
    signal.signal(signal.SIGCHLD,handleSIGCHLD)

    parser = argparse.ArgumentParser()
    parser.add_argument("--pidfile", default=".streaming.pid")
    args = parser.parse_args()

    if Config.isStreamingSocketEnabled():
        print "Starting streaming server"
        with util.PidFile(args.pidfile):
            startStreamingServer()
    else:
        print "Streaming is not enabled"

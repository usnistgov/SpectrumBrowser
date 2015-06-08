import struct
from io import BytesIO
import binascii
from bson.json_util import dumps
import util
import authentication
import json
import time
import gevent
from DataStreamSharedState import MemCache
from Queue import Queue
import populate_db
import numpy as np
import threading
import sys
import traceback
import socket
import ssl
from Defines import MAX_HOLD
from Defines import SYS
from Defines import LOC
from Defines import DATA
from Defines import TYPE
from Defines import SENSOR_ID
from Defines import SENSOR_KEY
from Defines import SPECTRUMS_PER_FRAME
from Defines import STREAMING_FILTER
from Defines import OCCUPANCY_START_TIME
from Defines import ENABLED
from Defines import SYS_TO_DETECT
from Defines import DISABLED
import SensorDb
import DataMessage
from multiprocessing import Process
import Config
import zmq
import os
import signal
import argparse






isSecure = True
memCache = None

lastDataMessage={}
lastDataMessageInsertedAt={}
lastDataMessageReceivedAt={}
lastDataMessageOriginalTimeStamp={}
WAITING_FOR_NEXT_INTERVAL = 1
BUFFERING = 2
POSTING = 3
APPLY_DRIFT_CORRECTION = False




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
    
    def close(self):
        self.buf.close()


                

        


# Socket IO for reading from sensor. TODO : make this a secure socket.
class MySocketServer(threading.Thread):
    def __init__(self,socket,port):
        threading.Thread.__init__(self)
        self.socket = socket
        self.streamingPort = port
        
    def run(self):
        while True:
            util.debugPrint("Starting socket server on "+ str(self.streamingPort))
            (conn,addr) = self.socket.accept()
            if isSecure:
                try :
                    cert = Config.getCertFile()
                    c = ssl.wrap_socket(conn,server_side = True, certfile = cert, ssl_version=ssl.PROTOCOL_SSLv3  )
                    t = Process(target=workerProc,args=(c,))  
                    t.start()
                except:
                    traceback.print_exc()
                    conn.close()
                    util.debugPrint( "DataStreaming: Unexpected error")
                    continue
            else:
                t = Process(target=workerProc,args=(conn,))
                util.debugPrint("MySocketServer Accepted a connection from "+str(addr))
                t.start()
        
        
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
    if memCache == None :
       memCache = MemCache()
    bbuf = BBuf(conn)
    readFromInput(bbuf)


def getSensorData(ws):
    """

    Handle sensor data streaming requests from the web browser.

    """
    try :
        util.debugPrint( "DataStreamng:getSensorData")
        global memCache
        if memCache == None:
            memCache = MemCache()
        token = ws.receive()
        print "token = " , token
        parts = token.split(":")
        if parts == None or len(parts) < 5:
            ws.close()
            return
        sessionId = parts[0]
        if not authentication.checkSessionId(sessionId,"user"):
            ws.close()
            return
        sensorId = parts[1]
        systemToDetect  = parts[2]
        minFreq = int(parts[3])
        maxFreq = int(parts[4])
        util.debugPrint("sensorId " + sensorId )
        sensorObj = SensorDb.getSensorObj(sensorId)
        if sensorObj == None:
            ws.send(dumps({"status": "Sensor not found : " + sensorId}))
            
        bandName = systemToDetect + ":" + str(minFreq) + ":" + str(maxFreq)
        util.debugPrint("isStreamingEnabled = " + str(sensorObj.isStreamingEnabled()))
        lastDataMessage = memCache.loadLastDataMessage(sensorId,bandName)
        key = sensorId + ":" + bandName
        if not key in lastDataMessage or not sensorObj.isStreamingEnabled() :
            ws.send(dumps({"status":"NO_DATA : Data message not found or streaming not enabled"}))
        else:
            ws.send(dumps({"status":"OK"}))
            ws.send(str(lastDataMessage[key]))
            lastdatatime = -1
            drift = 0
            while True:
                secondsPerFrame = sensorObj.getStreamingSecondsPerFrame()
                lastdataseen = memCache.loadLastDataSeenTimeStamp(sensorId,bandName)
                if key in lastdataseen and lastdatatime != lastdataseen[key]:
                    lastdatatime = lastdataseen[key]
                    sensordata = memCache.loadSensorData(sensorId,bandName)
                    memCache.incrementDataConsumedCounter(sensorId,bandName)
                    currentTime = time.time()
                    lastdatasent = currentTime
                    drift = drift + (currentTime - lastdatasent) - secondsPerFrame
                    ws.send(sensordata[key])
                    # If we drifted, send the last reading again to fill in.
                    if drift < 0:
                        drift = 0
                    if drift > secondsPerFrame:
                        if APPLY_DRIFT_CORRECTION:
                            util.debugPrint("Drift detected")
                            ws.send(sensordata[key])
                        drift = 0
                sleepTime = secondsPerFrame
                gevent.sleep(sleepTime)
    except:
        traceback.print_exc()
        ws.close()
        util.debugPrint("Error writing to websocket")



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
                isStreamingCaptureEnabled = sensorObj.isStreamingCaptureEnabled()
                sensorData = [0 for i in range(0,samplesPerCapture)]
                spectrumsPerFrame = 1
                jsonData[SPECTRUMS_PER_FRAME] = spectrumsPerFrame
                jsonData[STREAMING_FILTER] = sensorObj.getStreamingFilter()
                bandName = DataMessage.getFreqRange(jsonData)        
                # Keep a copy of the last data message for periodic insertion into the db         
                memCache.setLastDataMessage(sensorId,bandName,json.dumps(jsonData))
                bufferCounter = 0
                globalCounter = 0
                prevOccupancyArray = [0 for i in range(0,n)]
                occupancyArray = [0 for i in range(0,n)]
                occupancyTimer = time.time()
                if not sensorId in lastDataMessage:
                    lastDataMessage[sensorId] = jsonData              
                powerVal = [0 for i in range(0,n)]
                
                startTime = time.time()
                while True:
                        sensorObj = SensorDb.getSensorObj(sensorId)
                        if sensorObj == None:
                            raise Exception("Sensor not found")
                        if sensorObj.getSensorStatus() == DISABLED :
                            bbuf.close()
                            raise Exception("Sensor is disabled")
                        if not sensorObj.isStreamingEnabled():
                            raise Exception("Streaming is disabled")
                            
                        data = bbuf.readByte()
                        globalCounter = globalCounter + 1
                        sensorData[bufferCounter] = data
                        bufferCounter = bufferCounter + 1
                        powerVal[globalCounter % n] = data
                        now = time.time()
                        if bufferCounter == samplesPerCapture:
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
                            lastDataMessage[sensorId][OCCUPANCY_START_TIME] = occupancyTimer
                            headerStr = json.dumps(lastDataMessage[sensorId],indent=4)
                            headerLength = len(headerStr)
                            if sensorObj.isStreamingCaptureEnabled():
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
                     
                            
                        if globalCounter%n == 0 and memCache.getSubscriptionCount(sensorId) != 0:
                            if not np.array_equal(occupancyArray,prevOccupancyArray):
                                soc.send_pyobj({sensorId:occupancyArray})
                            prevOccupancyArray = np.array(occupancyArray)
                         
                        # sending data as CSV values to the browser
                        sensordata = str(powerVal)[1:-1].replace(" ", "")
                        memCache.setSensorData(sensorId,bandName,sensordata)
                        # Record the occupancy for the measurements.
                        if globalCounter % n == 0 :
                            # Allow for 10% jitter.
                            if now - startTime < timePerMeasurement/2 or now - startTime > timePerMeasurement*2 :
                                print " delta ", now - startTime, "global counter ", globalCounter
                                util.errorPrint("Data coming in too fast - sensor configuration problem.")
                                raise Exception("Data coming in too fast - sensor configuration problem.")
                            else:
                                startTime = now
                        lastdataseen  = now
                        memCache.setLastDataSeenTimeStamp(sensorId,bandName,lastdataseen)
                        memCache.incrementDataProducedCounter(sensorId,bandName)
            elif jsonData[TYPE] == SYS:
                util.debugPrint("DataStreaming: Got a System message -- adding to the database")
                populate_db.put_data(jsonStringBytes, headerLength)
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

def getSocketServerPort(sensorId):
    
    retval = {}
    global memCache
    if memCache == None:
        memCache = MemCache()
    numberOfWorkers = memCache.getNumberOfWorkers()
    sensor = SensorDb.getSensorObj(sensorId)
    if sensor == None or sensor.getSensorStatus() != ENABLED or numberOfWorkers == 0 \
        or not sensor.isStreamingEnabled():
        retval["port"] = -1
        return retval
    
    index = hash(sensorId) % numberOfWorkers
    retval["port"] = memCache.getSocketServerPorts()[index]
    return retval

def getSpectrumMonitoringPort(sensorId):
    retval = {}
    global memCache
    if memCache == None:
        memCache = MemCache()
    numberOfWorkers = memCache.getNumberOfWorkers()
    index = hash(sensorId) % numberOfWorkers
    retval["port"] = memCache.getSocketServerPorts()[index]+1
    return retval

def signal_handler(signal, frame):
        print('Caught signal! Exitting.')
        os._exit(0)

def startStreamingServer():
    # The following code fragment is executed when the module is loaded.
    global memCache
    if memCache == None :
        memCache = MemCache()
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
        socketServer = MySocketServer(soc,socketServerPort)
        socketServer.start()
    else:
        util.errorPrint( "DataStreaming: Streaming disabled on worker - no port found.")

if __name__ == '__main__':
    signal.signal(signal.SIGINT,signal_handler)

    parser = argparse.ArgumentParser()
    parser.add_argument("--pidfile", default=".streaming.pid")
    args = parser.parse_args()

    if Config.isStreamingSocketEnabled():
        print "Starting streaming server"
        with util.PidFile(args.pidfile):
            startStreamingServer()
    else:
        print "Streaming is not enabled"

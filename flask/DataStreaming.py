import struct
from io import BytesIO
import binascii
from bson.json_util import dumps
import util
import authentication
import json
import time
import gevent
import memcache
from Queue import Queue
import populate_db
import numpy as np
import Config
import threading
import sys
import traceback
import socket
from flaskr import jsonify


memCache = None
socketServerPort = -1

lastDataMessage={}
lastDataMessageInsertedAt={}
lastDataMessageReceivedAt={}
lastDataMessageOriginalTimeStamp={}
WAITING_FOR_NEXT_INTERVAL = 1
BUFFERING = 2
POSTING = 3




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




# Socket IO for reading from sensor. TODO : make this a secure socket.
class MySocketServer(threading.Thread):
    def __init__(self,socket,port):
        threading.Thread.__init__(self)
        self.socket = socket
        self.streamingPort = port


    def run(self):
        while True:
            try :
                print "Accepting connections on port ",self.streamingPort
                (conn,addr) = self.socket.accept()
                util.debugPrint("MySocketServer Accepted a connection from "+str(addr))
                t = Worker(conn)
                t.start()
            except:
                traceback.print_exc()
                raise

class Worker(threading.Thread):
    def __init__(self,conn):
        threading.Thread.__init__(self)
        self.conn = conn
        self.buf = BytesIO()

    def run(self):
        try:
            readFromInput(self,False)
        except:
            print "error reading sensor socket:", sys.exc_info()[0]
            self.conn.close()
            return


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



class MemCache:
    """
    Keeps a memory map of the data pushed by the sensor so it is accessible
    by any of the flask worker processes.
    """
    def acquire(self):
        while True:
            key = "lockCounter"
            counter = self.mc.gets(key)
            assert counter is not None, 'Uninitialized counter'
            if self.mc.cas(key, counter+1):
                break

    def release(self):
        self.mc.decr("lockCounter")

    def __init__(self):
       self.mc = memcache.Client(['127.0.0.1:11211'], debug=0,cache_cas=True)
       self.lastDataMessage = {}
       self.lastdataseen = {}
       self.sensordata = {}
       self.dataCounter = {}
       self.mc.set("dataCounter",self.dataCounter)
       self.mc.set("lockCounter", 0)




    def loadLastDataMessage(self):
        self.acquire()
        try :
            self.lastDataMessage = self.mc.get("lastDataMessageSeen")
            if self.lastDataMessage == None:
                self.lastDataMessage = {}
            return self.lastDataMessage
        finally:
            self.release()

    def loadSensorData(self):
        self.acquire()
        try:
            self.sensordata = self.mc.get("sensordata")
            if self.sensordata == None:
                self.sensordata = {}
            return self.sensordata
        finally:
            self.release()

    def loadLastDataSeenTimeStamp(self):
        self.acquire()
        try:
            self.lastdataseen = self.mc.get("lastdataseen")
            if self.lastdataseen == None:
                self.lastdataseen = {}
            return self.lastdataseen
        finally:
            self.release()
    def setLastDataMessage(self,sensorId,message):
        self.acquire()
        try:
            self.loadLastDataMessage()
            self.lastDataMessage[sensorId] = message
            self.mc.set("lastDataMessageSeen",self.lastDataMessage)
        finally:
            self.release()

    def setSensorData(self,sensorId,data):
        self.acquire()
        try :
            self.loadSensorData()
            self.sensordata[sensorId] = data
            self.mc.set("sensordata",self.sensordata)
        finally:
            self.release()

    def incrementDataProducedCounter(self,sensorId):
        self.acquire()
        try:
            self.dataCounter = self.mc.get("dataCounter")
            if sensorId in self.dataCounter:
                count = self.dataCounter[sensorId]
                count = count+1
            else:
                count = 1
            self.dataCounter[sensorId] = count
            self.mc.set("dataCounter",self.dataCounter)
        finally:
            self.release()

    def decrementDataProducedCounter(self,sensorId):
        self.acquire()
        try:
            self.dataCounter = self.mc.get("dataCounter")
            if sensorId in self.dataCounter:
                count = self.dataCounter[sensorId]
                count = count - 1
            else:
                count = 0
            self.dataCounter[sensorId] = count
            self.mc.set("dataCounter",self.dataCounter)
            print "Data counter value for ",sensorId, count
        finally:
            self.release()



    def setLastDataSeenTimeStamp(self,sensorId,timestamp):
        self.acquire()
        try:
            self.loadLastDataSeenTimeStamp()
            self.lastdataseen[sensorId] = timestamp
            self.mc.set("lastdataseen",self.lastdataseen)
        finally:
            self.release()



def getSensorData(ws):
    """

    Handle sensor data streaming requests from the web browser.

    """
    try :
        print "DataStreamng:getSensorData"
        global memCache
        if memCache == None:
            memCache = MemCache()
        token = ws.receive()
        print "token = " , token
        parts = token.split(":")
        sessionId = parts[0]
        if not authentication.checkSessionId(sessionId):
            ws.close()
            return
        sensorId = parts[1]
        util.debugPrint("sensorId " + sensorId)

        lastDataMessage = memCache.loadLastDataMessage()
        if not sensorId in lastDataMessage :
            ws.send(dumps({"status":"NO_DATA"}))
        else:
            ws.send(dumps({"status":"OK"}))
            ws.send(lastDataMessage[sensorId])
            lastdatatime = -1
            while True:
                lastdataseen = memCache.loadLastDataSeenTimeStamp()
                if lastdatatime != lastdataseen[sensorId]:
                    lastdatatime = lastdataseen[sensorId]
                    sensordata = memCache.loadSensorData()
                    memCache.decrementDataProducedCounter(sensorId)
                    ws.send(sensordata[sensorId])
                gevent.sleep(Config.getStreamingSecondsPerFrame())
    except:
        ws.close()
        print "Error writing to websocket"



def readFromInput(bbuf,isWebSocket):
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
         print dumps(jsonData, sort_keys=True, indent=4)
         # the last time a data message was inserted
         if jsonData["Type"] == "Data":
             try:
                state = BUFFERING
                n = jsonData["mPar"]["n"]
                sensorId = jsonData["SensorID"]
                lastDataMessageReceivedAt[sensorId] = time.time()
                lastDataMessageOriginalTimeStamp[sensorId] = jsonData['t']
                #TODO New parameter should be added to data message.
                timePerMeasurement = jsonData["mPar"]["tm"]
                # TODO -- this needs to be configurable
                sensorData = [0 for i in range(0,Config.getStreamingCaptureSampleSize()*n)]
                spectrumsPerFrame = int(Config.getStreamingSecondsPerFrame() / timePerMeasurement)
                measurementsPerFrame = spectrumsPerFrame * n
                jsonData["spectrumsPerFrame"] = spectrumsPerFrame
                jsonData["StreamingFilter"] = Config.getStreamingFilter()
                # Keep a copy of the last data message for periodic insertion into the db
                memCache.setLastDataMessage(sensorId,json.dumps(jsonData))
                util.debugPrint("measurementsPerFrame : " + str(measurementsPerFrame) + " n = " + str(n) + " spectrumsPerFrame = " + str(spectrumsPerFrame))
                bufferCounter = 0
                globalCounter = 0
                while True:
                    startTime = time.time()
                    if Config.getStreamingFilter() == "PEAK":
                        powerVal = [-100 for i in range(0, n)]
                    else:
                        powerVal = [0 for i in range(0, n)]
                    for i in range(0, measurementsPerFrame):
                        data = bbuf.readByte()
                        globalCounter = globalCounter + 1
                        if not sensorId in lastDataMessage:
                           lastDataMessage[sensorId] = jsonData
                        if state == BUFFERING :
                            sensorData[bufferCounter] = data
                            bufferCounter = bufferCounter + 1
                            if bufferCounter == Config.getStreamingCaptureSampleSize()*n:
                                state = POSTING
                        elif state == POSTING:
                            # Buffer is full so push the data into mongod.
                            print "Inserting Data message"
                            bufferCounter = 0
                            # Time offset since the last data message was received.
                            timeOffset = time.time() - lastDataMessageReceivedAt[sensorId]
                            # Offset the capture by the time since the DataMessage header was received.
                            lastDataMessage[sensorId]["t"] = lastDataMessageOriginalTimeStamp[sensorId] +\
                                                                int(timeOffset)
                            lastDataMessage[sensorId]["nM"] = Config.getStreamingCaptureSampleSize()
                            lastDataMessage[sensorId]['mPar']["td"] = int(Config.getStreamingCaptureSampleSize() * timePerMeasurement)
                            headerStr = json.dumps(lastDataMessage[sensorId],indent=4)
                            headerLength = len(headerStr)
                            # Start the db operation in a seperate thread.
                            lastDataMessageInsertedAt[sensorId] = time.time()
                            thread = threading.Thread(target=populate_db.put_data, \
                                                      args=(headerStr,headerLength),\
                                            kwargs={"filedesc":None,"powers":sensorData})
                            thread.start()
                            state = WAITING_FOR_NEXT_INTERVAL
                        elif state == WAITING_FOR_NEXT_INTERVAL :
                            now = time.time()
                            delta = now - lastDataMessageInsertedAt[sensorId]
                            # Only buffer data when we are at a boundary.
                            if delta > Config.getStreamingSamplingIntervalSeconds() \
                               and globalCounter % n == 0 :
                               state = BUFFERING
                        if Config.getStreamingFilter() == "PEAK":
                            powerVal[i % n] = np.maximum(powerVal[i % n], data)
                        else:
                            powerVal[i % n] += data
                    if Config.getStreamingFilter() != "PEAK":
                        for i in range(0, len(powerVal)):
                            powerVal[i] = powerVal[i] / spectrumsPerFrame
                    # sending data as CSV values.
                    sensordata = str(powerVal)[1:-1].replace(" ", "")
                    memCache.setSensorData(sensorId,sensordata)
                    lastdataseen  = time.time()
                    memCache.setLastDataSeenTimeStamp(sensorId,lastdataseen)
                    memCache.incrementDataProducedCounter(sensorId)
                    endTime = time.time()
                    if isWebSocket:
                        delta = 0.7 * Config.getStreamingSecondsPerFrame() - endTime + startTime
                        if delta > 0:
                            gevent.sleep(delta)
                        else:
                            gevent.sleep(0.7 * Config.getStreamingSecondsPerFrame())
             except:
                print "Unexpected error:", sys.exc_info()[0]
                print sys.exc_info()
                traceback.print_exc()
                raise

         elif jsonData["Type"] == "Sys":
            print "Got a System message -- adding to the database"
            populate_db.put_data(jsonStringBytes, headerLength)
         elif jsonData["Type"] == "Loc":
            print "Got a Location Message -- adding to the database"
            populate_db.put_data(jsonStringBytes, headerLength)




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

def getSocketServerPort():
    retval = {}
    retval["port"] = socketServerPort
    return jsonify(retval),200


# The following code fragment is executed when the module is loaded.
if Config.isStreamingSocketEnabled():
    print "Starting streaming server"
    if memCache == None :
        memCache = MemCache()
    port = Config.getStreamingServerPort()
    socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    portAssigned = False
    for p in range(port,port+10,1):
        try :
            print 'Trying port ',p
            socket.bind(('0.0.0.0',p))
            socket.listen(10)
            socketServerPort = p
            portAssigned = True
            break
        except:
            print 'Bind failed.'
    if portAssigned:
        socketServer = MySocketServer(socket,socketServerPort)
        socketServer.start()


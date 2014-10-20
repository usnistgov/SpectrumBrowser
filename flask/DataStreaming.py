import flaskr as main
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
from threading import Thread
import sys
import traceback

peakDetection = True

memCache = None

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

    def size(self):
        return self.size


class MemCache:
    """
    Keeps a memory map of the data pushed by the sensor so it is accessible
    by any of the flask worker processes.
    """


    def __init__(self):
       self.mc = memcache.Client(['127.0.0.1:11211'], debug=0)
       self.lastDataMessage = {}
       self.lastdataseen = {}
       self.sensordata = {}



    def loadLastDataMessage(self):
        self.lastDataMessage = self.mc.get("lastDataMessageSeen")
        if self.lastDataMessage == None:
            self.lastDataMessage = {}
        return self.lastDataMessage

    def loadSensorData(self):
        self.sensordata = self.mc.get("sensordata")
        if self.sensordata == None:
            self.sensordata = {}
        return self.sensordata

    def loadLastDataSeenTimeStamp(self):
        self.lastdataseen = self.mc.get("lastdataseen")
        if self.lastdataseen == None:
            self.lastdataseen = {}
        return self.lastdataseen

    def setLastDataMessage(self,sensorId,message):
        self.loadLastDataMessage()
        self.lastDataMessage[sensorId] = message
        self.mc.set("lastDataMessageSeen",self.lastDataMessage)

    def setSensorData(self,sensorId,data):
        self.loadSensorData()
        self.sensordata[sensorId] = data
        self.mc.set("sensordata",self.sensordata)

    def setLastDataSeenTimeStamp(self,sensorId,timestamp):
        self.loadLastDataSeenTimeStamp()
        self.lastdataseen[sensorId] = timestamp
        self.mc.set("lastdataseen",self.lastdataseen)



def getSensorData(ws):
    """

    Handle sensor data streaming requests from the web browser.

    """
    try :
        print "getSensorData"
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
                    ws.send(sensordata[sensorId])
                gevent.sleep(main.SECONDS_PER_FRAME)
    except:
        ws.close()
        print "Error writing to websocket"







def dataStream(ws):
     """
     Handle the data stream from a sensor.
     """
     print "Got a connection"
     bbuf = MyByteBuffer(ws)
     global memCache
     if memCache == None :
         memCache = MemCache()

     while True:
         lengthString = ""
         while True:
             lastChar = bbuf.readChar()
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
                 # Keep a copy of the last data message for periodic insertion into the db
                 memCache.setLastDataMessage(sensorId,jsonStringBytes)
                 #TODO New parameter should be added to data message.
                 timePerMeasurement = jsonData["mPar"]["tm"]
                 # TODO -- this needs to be configurable
                 sensorData = [0 for i in range(0,Config.STREAMING_CAPTURE_SAMPLE_SIZE*n)]
                 spectrumsPerFrame = int(main.SECONDS_PER_FRAME / timePerMeasurement)
                 measurementsPerFrame = spectrumsPerFrame * n
                 util.debugPrint("measurementsPerFrame : " + str(measurementsPerFrame) + " n = " + str(n) + " spectrumsPerFrame = " + str(spectrumsPerFrame))
                 bufferCounter = 0
                 while True:
                     startTime = time.time()
                     if peakDetection:
                         powerVal = [-100 for i in range(0, n)]
                     else:
                         powerVal = [0 for i in range(0, n)]
                     for i in range(0, measurementsPerFrame):
                         data = bbuf.readByte()
                         if not sensorId in lastDataMessage:
                            lastDataMessage[sensorId] = jsonData
                         # TODO -- make the sampling interval configurable
                         if state == BUFFERING :
                             sensorData[bufferCounter] = data
                             bufferCounter = bufferCounter + 1
                             if bufferCounter == Config.STREAMING_CAPTURE_SAMPLE_SIZE*n:
                                 state = POSTING
                         elif state == POSTING:
                             # Buffer is full so push the data into mongod.
                             print "Inserting Data message"
                             bufferCounter = 0
                             # Time offset since the last data message was received.
                             timeOffset = time.time() - lastDataMessageReceivedAt[sensorId]
                             # Offset the capture by the time since the DataMessage header was received.
                             lastDataMessage[sensorId]["t"] = lastDataMessageOriginalTimeStamp[sensorId] + int(timeOffset)
                             lastDataMessage[sensorId]["nM"] = Config.STREAMING_CAPTURE_SAMPLE_SIZE
                             lastDataMessage[sensorId]['mPar']["td"] = int(Config.STREAMING_CAPTURE_SAMPLE_SIZE * timePerMeasurement)
                             headerStr = json.dumps(lastDataMessage[sensorId],indent=4)
                             headerLength = len(headerStr)
                             # Start the db operation in a seperate thread.
                             lastDataMessageInsertedAt[sensorId] = time.time()
                             thread = Thread(target=populate_db.put_data, args=(headerStr,headerLength),\
                                             kwargs={"filedesc":None,"powers":sensorData})
                             thread.start()
                             state = WAITING_FOR_NEXT_INTERVAL
                         elif state == WAITING_FOR_NEXT_INTERVAL :
                             now = time.time()
                             delta = now - lastDataMessageInsertedAt[sensorId]
                             if delta > Config.STREAMING_SAMPLING_INTERVAL_SECONDS:
                                 state = BUFFERING
                         if peakDetection:
                             powerVal[i % n] = np.maximum(powerVal[i % n], data)
                         else:
                             powerVal[i % n] += data
                     if not peakDetection:
                         for i in range(0, len(powerVal)):
                             powerVal[i] = powerVal[i] / spectrumsPerFrame
                     # sending data as CSV values.
                     sensordata = str(powerVal)[1:-1].replace(" ", "")
                     memCache.setSensorData(sensorId,sensordata)
                     lastdataseen  = time.time()
                     memCache.setLastDataSeenTimeStamp(sensorId,lastdataseen)
                     endTime = time.time()
                     delta = 0.7 * main.SECONDS_PER_FRAME - endTime + startTime
                     if delta > 0:
                         gevent.sleep(delta)
                     else:
                         gevent.sleep(0.7 * main.SECONDS_PER_FRAME)
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

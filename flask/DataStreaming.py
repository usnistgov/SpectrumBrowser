import flaskr as main
import struct
from io import BytesIO
import binascii
from bson.json_util import dumps
import util
import authentication
from Queue import Queue
import json
import time
import numpy as np
import gevent

peakDetection = True
lastDataMessage = {}
sensordata = {}
lastdataseen = {}

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
        if not authentication.checkSessionId(sessionId):
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
            spectrumsPerFrame = int(main.SECONDS_PER_FRAME / timePerMeasurement)
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
                delta = 0.7 * main.SECONDS_PER_FRAME - endTime + startTime
                if delta > 0:
                    gevent.sleep(delta)
                else:
                    gevent.sleep(0.7 * main.SECONDS_PER_FRAME)
                # print "count " , count
        elif jsonData["Type"] == "Sys":
            print "Got a System message"
        elif jsonData["Type"] == "Loc":
            print "Got a Location Message"

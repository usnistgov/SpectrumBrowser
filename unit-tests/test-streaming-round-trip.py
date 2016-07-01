#! /usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
#This software was developed by employees of the National Institute of
#Standards and Technology (NIST), and others. 
#This software has been contributed to the public domain. 
#Pursuant to title 15 Untied States Code Section 105, works of NIST
#employees are not subject to copyright protection in the United States
#and are considered to be in the public domain. 
#As a result, a formal license is not needed to use this software.
# 
#This software is provided "AS IS."  
#NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
#OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
#MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
#AND DATA ACCURACY.  NIST does not warrant or make any representations
#regarding the use of the software or the results thereof, including but
#not limited to the correctness, accuracy, reliability or usefulness of
#this software.


import argparse
import socket
import requests
import sys
import time
import ssl
import threading
from websocket import create_connection
import os
from bson.json_util import loads, dumps
import numpy as np
from collections import deque

secure = True

STATUS_MESSAGE_NOT_SEEN = 1
STATUS_MESSAGE_SEEN = 3
DATA_MESSAGE_SEEN = 4

errorFlag = False


class ReceiverThread(threading.Thread):
    def __init__(self, sensorId, SessionToken, freqRange, runLength, semaphore, timingQueue):
        super(ReceiverThread, self).__init__()
        if secure:
            self.ws = create_connection("wss://localhost:8443/sensordata", sslopt=dict(cert_reqs=ssl.CERT_NONE))
        else:
            self.ws = create_connection("ws://127.0.0.1:8000/sensordata")
        token = SessionToken + ":" + sensorId + ":" + freqRange
        self.ws.send(token)
        self.state = STATUS_MESSAGE_NOT_SEEN
        self.delta = []
        self.interArrivalTime = []
        self.runLength = runLength
        self.count = 0
        self.timingQueue = timingQueue
        self.semaphore = semaphore
        if semaphore != None:
            semaphore.acquire(True)  # decrements the counter


    def run(self):
        time.sleep(1)
        while True:
            data = self.ws.recv()
            if self.state == STATUS_MESSAGE_NOT_SEEN:
                print "message = ", str(data)
                jsonObj = loads(str(data))
                if jsonObj["status"] == "NO_DATA":
                    print data
                    print "NO DATA -- restart test case."
                    errorFlag = True
                    os._exit(0)
                else:
                    self.state = STATUS_MESSAGE_SEEN
                # print "Status Message seen at receiver "
            elif self.state == STATUS_MESSAGE_SEEN:
                jsonObj = loads(str(data))
                self.state = DATA_MESSAGE_SEEN
                # print "Data Message seen at receiver for ", jsonObj["SensorID"]
                nFreqBins = jsonObj["mPar"]["n"]
                # print nFreqBins
                global spectrumsPerFrame
                spectrumsPerFrame = jsonObj["_spectrumsPerFrame"]
                if self.semaphore != None:
                    self.semaphore.release()
            else:
                self.count = self.count + 1
                recvTime = time.time()
                if self.timingQueue == None:
                    # no timing queue means we are just a load generation client
                    if self.count >= self.runLength:
                        break
                    else:
                        continue
                if  len(self.timingQueue) == 0:
                    if self.count == 1:
                        print "Empty timing queue detected this is normal -- will occur on first cache read"
                        continue
                    else:
                        print "Consumer got ahead of producer -- check server and ensure DataStreaming.APPLY_DRIFT_CORRECTION = False"
                        continue
                sendTime = self.timingQueue.popleft()
                delta = recvTime - sendTime

                # skip the first 10 values to let the pipeline settle down.
                if self.count > 10 :
                    self.delta.append(delta)
                    interArrivalTime = time.time() - self.recvTime
                    self.interArrivalTime.append(interArrivalTime)
                self.recvTime = recvTime
                if self.count >= self.runLength:
                    self.ws.close()
                    nparray = np.array(self.delta)
                    mean = np.mean(nparray)
                    jitter = np.std(nparray)
                    median = np.median(nparray)
                    max = np.max(nparray)
                    print "=============================================================="
                    print "           TEST RESULTS                                       "
                    print "Note: First 10 samples are discarded to let pipeline settle."
                    print "=============================================================="
                    print "Round trip delay : "
                    print "Sample size = ", len(self.delta), " Mean = ", mean , "s; Median = ", median , "s; Max = ", max, \
                        "s; Std. Deviation = ", jitter; "s"
                    print ("95% confidence interval:")
                    delta = []
                    for timing in self.delta:
                        if timing > mean - 2 * jitter and timing < mean + 2 * jitter:
                            delta.append(timing)
                    nparray = np.array(delta)
                    mean = np.mean(nparray)
                    jitter = np.std(nparray)
                    median = np.median(nparray)
                    max = np.max(nparray)
                    print "Sample size = ", len(delta), " Mean = ", mean , "s; Median = ", median , "s; Max = ", max, \
                        "s; Std. Deviation = ", jitter; "s"
                    print "=============================================================="
                    print "Interarrival Time:"
                    nparray = np.array(self.interArrivalTime)
                    mean = np.mean(nparray)
                    jitter = np.std(nparray)
                    median = np.median(nparray)
                    max = np.max(nparray)
                    print "Sample size = ", len(self.interArrivalTime), " Mean = ", mean , "s; Median = ", median , "s; Max = ", max, \
                        "s; Std. Deviation = ", jitter; "s"
                    print ("95% confidence interval:")
                    delta = []
                    for timing in self.interArrivalTime:
                        if timing > mean - 2 * jitter and timing < mean + 2 * jitter:
                            delta.append(timing)
                    nparray = np.array(delta)
                    mean = np.mean(nparray)
                    jitter = np.std(nparray)
                    median = np.median(nparray)
                    max = np.max(nparray)
                    print "Sample size = ", len(delta), " Mean = ", mean , "s; Median = ", median , "s; Max = ", max, \
                        "s; Std. Deviation = ", jitter; "s"
                    print "=============================================================="

                    os._exit(0)




if __name__ == "__main__":
    print "Run this script twice - the first time to prime the server"
    global SessionToken
    global sensorId
    parser = argparse.ArgumentParser(description="Process command line args")
    parser.add_argument("-data", help="File name to stream from ")
    parser.add_argument("-sensorId", help="SensorId")
    parser.add_argument("-dataLength", help="Number of spectrum lines to stream")
    parser.add_argument("-nConsumers", help="Number of simulated web browser clients")
    parser.add_argument("-baseUrl", help="Access URL for spectrumbrowser")


    args = parser.parse_args()
    filename = args.data
    sensorId = args.sensorId
    url = args.baseUrl
    if url == None:
        url = "http://localhost:8000"

    if args.nConsumers == None:
        nConsumers = 1
    else :
        nConsumers = int(args.nConsumers)

    if nConsumers < 1 :
        print "Specify nConsumers >= 1"
        os._exit(0)

    if sensorId == None:
        print "sensorId is missing"
        os._exit(0)

    dataLength = args.dataLength
    if dataLength == None:
        runLength = 1000
    else:
        runLength = int(dataLength)




    if filename == None:
        print "please specify -data filename"
        os._exit(0)
    if sensorId == None:
        print "Please specify -sensor id"

    print "==================================================================="
    print "Test Parameters "
    print "baseUrl = ", url
    print "sensorId = ", sensorId
    print "dataLength = ", runLength
    print "nConsumers = ", nConsumers
    print "data = ", filename

    r = requests.post(url + "/spectrumbrowser/isAuthenticationRequired")
    json = r.json()
    if json["AuthenticationRequired"] :
        print ("please disable authentication on the server and configure sensor for streaming")
        sys.exit()
    SessionToken = json["SessionToken"]
    r = requests.post(url + "/sensordata/getStreamingPort/" + sensorId)
    json = r.json()
    port = json["port"]
    print "port = ", port
    r = requests.post("http://localhost:8000/sensordb/getSensorConfig/" + sensorId)
    json = r.json()
    print json
    if json["status"] != "OK":
        print json["ErrorMessage"]
        os._exit()
    if not json["sensorConfig"]["isStreamingEnabled"]:
        print "Streaming is not enabled"
        print json
        os._exit(1)
    timeBetweenReadings = float(json["sensorConfig"]["streaming"]["streamingSecondsPerFrame"])
    freqRange = json["sensorConfig"]["thresholds"].keys()[0]
    print freqRange
    
    if not secure:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("localhost", port))
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock = ssl.wrap_socket(s, ca_certs="dummy.crt", cert_reqs=ssl.CERT_OPTIONAL)
        sock.connect(('localhost', port))
    semaphore = threading.BoundedSemaphore()
    queue = deque()
    threads = []
    for i in range (0, nConsumers):
        if i == 0:
            threads.append(ReceiverThread(sensorId, SessionToken, freqRange, runLength, semaphore, queue))
        else :
            threads.append(ReceiverThread(sensorId, SessionToken, freqRange, runLength, None, None))

    

    with open(filename, "r") as f:
        count = 0
        headerCount = 0
        nFreqBins = 0
        headerLengthStr = ""
        while True:
            readByte = f.read(1)
            if str(readByte) != "{":
                headerLengthStr = headerLengthStr + str(readByte)
            else:
                lengthToRead = int(headerLengthStr) - 1

                # stuff the sensor id with the given sensor ID in the command line
                toSend = f.read(lengthToRead)
                header = "{" + toSend
                parsedHeader = loads(header)
                if parsedHeader["Type"] == "Data":
                      nFreqBins = parsedHeader["mPar"]["n"]
                      # print "nFreqBins = ",nFreqBins
                parsedHeader["SensorID"] = sensorId
                toSend = dumps(parsedHeader, indent=4)
                headerLengthStr = str(len(toSend))
                sock.send(headerLengthStr)
                sock.send(toSend)
                headerLengthStr = ""
                headerCount = headerCount + 1
                if headerCount == 3 :
                    break

        for thread in threads:
            thread.start()
        semaphore.acquire(True)
        # print "spectrumsPerFrame = " , spectrumsPerFrame, " nFreqBins ", nFreqBins
        # print "Start"
        
        
        try:
            while True:
                count = count + 1
                if errorFlag :
                    sys.exit()
                    os.exit()
                    quit()
                global spectrumsPerFrame
                if count % spectrumsPerFrame == 0 :
                    sendTime = time.time()
                    queue.append(sendTime)
                toSend = f.read(nFreqBins)
                sock.send(toSend)
                time.sleep(timeBetweenReadings)
        except:
            os._exit(0)

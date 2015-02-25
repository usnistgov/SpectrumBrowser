import argparse
import socket
import requests
import sys
import time
import ssl
import threading
from websocket import create_connection
import json
import os
from bson.json_util import loads,dumps
import numpy as np
from collections import deque

secure = True

STATUS_MESSAGE_NOT_SEEN = 1
STATUS_MESSAGE_SEEN = 3
DATA_MESSAGE_SEEN = 4


class ReceiverThread(threading.Thread):
    def __init__(self, sensorId,SessionToken,runLength,semaphore,timingQueue):
        super(ReceiverThread,self).__init__()
        if secure:
            self.ws = create_connection("wss://localhost:8443/sensordata",sslopt=dict(cert_reqs=ssl.CERT_NONE))
        else:
            self.ws = create_connection("ws://127.0.0.1:8000/sensordata")
        token = SessionToken + ":" + sensorId
        self.ws.send(token)
        self.state =  STATUS_MESSAGE_NOT_SEEN
        self.delta = []
        self.runLength = runLength
        self.count = 0
        self.timingQueue = timingQueue
        self.semaphore = semaphore
       
        semaphore.acquire(True) # decrements the counter
      
    
    def run(self):
        time.sleep(.01)   
        while True:
            data = self.ws.recv()
            if self.state == STATUS_MESSAGE_NOT_SEEN:
                print data
                jsonObj = loads(str(data))
                if jsonObj["status"] == "NO_DATA":
                    print "NO DATA"
                    sys.exit()
                    os.exit()
                else:
                    self.state = STATUS_MESSAGE_SEEN
            elif self.state == STATUS_MESSAGE_SEEN:
                jsonObj = loads(str(data))
                self.state = DATA_MESSAGE_SEEN
                print data
                nFreqBins = jsonObj["mPar"]["n"]
                print nFreqBins
                global spectrumsPerFrame
                spectrumsPerFrame = jsonObj["_spectrumsPerFrame"] 
                self.semaphore.release()
            else:
                self.count = self.count + 1
                if len(self.timingQueue) == 0:
                    continue
                recvTime = time.time()
                sendTime = self.timingQueue.popleft()
                delta = recvTime - sendTime
                
                # skip the first 10 values to let the pipeline settle down.
                if self.count > 10 :
                    self.delta.append(delta)
                if self.count >= self.runLength:
                    self.ws.close()
                    nparray = np.array(self.delta)
                    mean = np.mean(nparray)
                    median = np.median(nparray)
                    max = np.max(nparray)
                    jitter = np.std(nparray)
                    print "Round trip delay : "
                    print "Sample size = ", self.runLength, " Mean = ", mean , "s; Median = ", median , "s; Max = ", max, \
                        "s; Std. Deviation = ", jitter; "s"
                    sys.exit()
                    os.exit()
                
                
                    

if __name__ == "__main__":
    global SessionToken
    global sensorId
    parser = argparse.ArgumentParser(description="Process command line args")
    parser.add_argument("-data",help="File name to stream")
    parser.add_argument("-sensorId",help="SensorId")
    parser.add_argument("-dataLength",help="Number of spectra")
    
    
    args = parser.parse_args()
    filename = args.data
    sensorId = args.sensorId
    if sensorId == None:
        print "sensorId is missing"
        
    dataLength = args.dataLength
    if dataLength == None:
        runLength = 1000
    else:
        runLength = int(dataLength)
    
    
    if filename == None:
        print "please specify -data filename"
        sys.exit()
    if sensorId == None:
        print "Please specify -sensor id"
        
    r  = requests.post("http://localhost:8000/spectrumbrowser/isAuthenticationRequired")
    json = r.json()
    if json["AuthenticationRequired"] :
        print ("please disable authentication and configure sensor for streaming")
        sys.exit()
    SessionToken = json["SessionToken"]
    r = requests.post("http://localhost:8000/sensordata/getStreamingPort")
    json = r.json()
    port = json["port"]
    print "port = ", port
    if not secure:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("localhost",port))
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock = ssl.wrap_socket(s, ca_certs="dummy.crt",cert_reqs=ssl.CERT_OPTIONAL)
        sock.connect(('localhost', port))
    semaphore = threading.BoundedSemaphore()  
    queue  = deque()
    thread = ReceiverThread(sensorId,SessionToken,runLength,semaphore,queue)
    thread.start()
    
    

    with open(filename,"r") as f:
        count = 0
        headerCount = 0
        nFreqBins = 0
        headerLengthStr = ""
        while True:
            readByte = f.read(1)
            if str(readByte) != "{":
                headerLengthStr = headerLengthStr + str(readByte)
            else:
                lengthToRead = int(headerLengthStr) -1 
                
                # stuff the sensor id with the given sensor ID in the command line 
                toSend = f.read(lengthToRead)
                header = "{" + toSend
                parsedHeader = loads(header)
                if parsedHeader["Type"] == "Data":
                      nFreqBins = parsedHeader["mPar"]["n"]
                      print "nFreqBins = ",nFreqBins
                parsedHeader["SensorID"] = sensorId
                toSend = dumps(parsedHeader,indent = 4)
                headerLengthStr = str(len(toSend))
                sock.send(headerLengthStr)
                sock.send(toSend)
                headerLengthStr = ""
                headerCount = headerCount + 1
                if headerCount == 3 :
                    break
                
        semaphore.acquire(True)
        print "spectrumsPerFrame = " , spectrumsPerFrame, " nFreqBins ", nFreqBins
        while True:
            count = count + 1
            global spectrumsPerFrame
            if count % spectrumsPerFrame == 0 :
                sendTime = time.time()
                queue.append(sendTime)
            toSend = f.read(nFreqBins)
            sock.send(toSend)
            time.sleep(.0009)

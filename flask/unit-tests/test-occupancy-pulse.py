'''
Created on Mar 9, 2015

@author: local
'''
import sys
import time
import argparse
import traceback
import requests
import socket
import ssl
from bson.json_util import loads,dumps
from bitarray import bitarray
from threading import Thread
global secure
secure = True
from multiprocessing import Process
import urlparse
import os
import thread
import time
import json
import array
import threading
import numpy as np

systemMessage = '{"Preselector": {"fLowPassBPF": "NaN", "gLNA": "NaN", "fHighPassBPF": "NaN", "fLowStopBPF": "NaN", "enrND": "NaN", "fnLNA": "NaN", "fHighStopBPF": "NaN", "pMaxLNA": "NaN"}, "Ver": "1.0.9", "Antenna": {"lCable": 0.5, "phi": 0.0, "gAnt": 2.0, "bwV": "NaN", "fLow": "NaN", "Pol": "VL", "XSD": "NaN", "bwH": 360.0, "theta": "N/A", "Model": "Unknown (whip)", "fHigh": "NaN", "VSWR": "NaN"}, "SensorKey": "NaN", "t": 1413576259, "Cal": "N/A", "SensorID": "ECR16W4XS", "Type": "Sys", "COTSsensor": {"fMax": 4400000000.0, "Model": "Ettus USRP N210 SBX", "pMax": -10.0, "fn": 5.0, "fMin": 400000000.0}}'
locationMessage = '{"Ver": "1.0.9", "Mobility": "Stationary", "Lon": -77.215337000000005, "SensorKey": "NaN", "t": 1413576259, "TimeZone": "America/New_York", "Lat": 39.134374999999999, "SensorID": "ECR16W4XS", "Alt": 143.5, "Type": "Loc"}'
dataMessage = '{"a": 1, "Ver": "1.0.9", "Compression": "None", "SensorKey": "NaN", "Processed": "False", "nM": 1800000, "SensorID": "ECR16W4XS", "mPar": {"tm": 0.001, "fStart": 703967500.0, "Atten": 38.0, "td": 1800.0, "fStop": 714047500.0, "Det": "Average", "n": 56}, "Type": "Data", "ByteOrder": "N/A", "Comment": "Using hard-coded (not detected) system noise power for wnI", "OL": "NaN", "DataType": "Binary - int8", "wnI": -77.0, "t1": 1413576259, "mType": "FFT-Power", "t": 1413576259, "Ta": 3600.0}'

def registerForAlert(serverUrl,sensorId,quiet,resultsFile,tb):
    global sendTime
    deltaArray = []
    results = open(resultsFile,"a+")
    try:
        parsedUrl = urlparse.urlsplit(serverUrl)
        netloc = parsedUrl.netloc
        host = netloc.split(":")[0]
        url = serverUrl + "/sensordata/getMonitoringPort/" + sensorId
        print url
        r = requests.post(url,verify=False)
        json = r.json()
        port = json["port"]
        print "Receiving occupancy alert on port " + str(port)
        if secure:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock = ssl.wrap_socket(s, ca_certs="dummy.crt",cert_reqs=ssl.CERT_OPTIONAL)
            sock.connect((host, port))
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((parsedUrl.hostname(), port))
        request = {"SensorID":sensorId}
        req = dumps(request)
        sock.send(req)
        startTime = time.time()
        alertCounter = 0
        
        try:
            while True:
                try:
                    occupancy = sock.recv()
                    if occupancy == None or len(occupancy) == 0 :
                        break
                    a = bitarray(endian="big")
                    a.frombytes(occupancy)
                    if not quiet:
                        print a
                    alertCounter = alertCounter + 1
                    if alertCounter %2 == 1:
                        recvTime = time.time()
                        delta = recvTime - sendTime
                        #print "Delta = ",delta
                        deltaArray.append(delta)
                    
                except KeyboardInterrupt:
                    break
                if alertCounter % 100 == 0:
                    meanLatency = np.mean(deltaArray)
                    standardDeviation = np.std(deltaArray)
                    print "Mean latency = ",meanLatency, " Std Deviation = ",standardDeviation
                    results.write(str(tb) + "," + str(meanLatency) + "," + str(standardDeviation) + "\n")
                    results.flush()               
        finally:
            endTime = time.time()
            elapsedTime = endTime - startTime
            estimatedStorage = alertCounter * 7
            print "Elapsed time ",elapsedTime, " Seconds; ", " alertCounter = ",\
                     alertCounter , " Storage: Data ",estimatedStorage, " bytes"
                
            
    except:
        traceback.print_exc()
        raise
    
def sendHeader(sock,jsonHeader,sensorId):
    jsonObj = json.loads(jsonHeader)
    jsonObj["SensorID"] = sensorId
    encodedObj = json.dumps(jsonObj,indent=4)
    length = len(encodedObj)
    print "Length = ",length

    print "header : ",encodedObj
    length = len(encodedObj)
    sock.send(str(length)+"\n")
    sock.send(encodedObj)
    
    
def sendPulseStream(serverUrl,sensorId,tb):
    global secure
    global sendTime
    url = serverUrl + "/sensordata/getStreamingPort/" + sensorId
    print url
    r = requests.post(url,verify=False)
    json = r.json()
    port = json["port"]
    print "port = ", port
    parsedUrl = urlparse.urlsplit(serverUrl)
    netloc = parsedUrl.netloc
    host = netloc.split(":")[0]
    if not secure:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host,port))
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock = ssl.wrap_socket(s, ca_certs="dummy.crt",cert_reqs=ssl.CERT_OPTIONAL)
        sock.connect((host, port))

   
    sendHeader(sock,systemMessage,sensorId)
    sendHeader(sock,locationMessage,sensorId)
    sendHeader(sock,dataMessage,sensorId)
    sampleBytes = [-50 for i in range(0,56)]
    samples = array.array('b',sampleBytes)
    print "len(samples) ", len(samples)
    noiseFloorBytes = [-77 for i in range(0,56)]
    noiseFloor = array.array('b',noiseFloorBytes)
    print "len(noiseFloor) ",len(noiseFloor)
    for i in range(0,100000):
        time.sleep(.001)
        if i % tb == 0:
            sendTime = time.time()
            sock.send(samples)
        else:
            sock.send(noiseFloor)
    os._exit()


if __name__== "__main__":
    global secure
    global sendTime
    try :
        parser = argparse.ArgumentParser(description="Process command line args")
        parser.add_argument("-sensorId",help="Sensor ID for which we are interested in occupancy alerts")
        parser.add_argument("-quiet", help="Quiet switch", dest='quiet', action='store_true')
        parser.add_argument('-secure', help="Use HTTPS", dest= 'secure', action='store_true')
        parser.add_argument('-url', help='base url for server')
        parser.add_argument("-tb", help='time (miliseconds) between pulses')
        parser.add_argument("-f", help='Results file')
        parser.set_defaults(quiet=False)
        parser.set_defaults(secure=True)
        parser.set_defaults(tb='1000')
        parser.set_defaults(f="pulse-timing.out")
        args = parser.parse_args()
        sensorId = args.sensorId
        quietFlag = True
        quietFlag = args.quiet
        secure = args.secure
        resultsFile = args.f
        tb = int(args.tb)
        url = args.url
            
       
        if url == None:     
            if secure:
                url= "https://localhost:8443"
            else:
                url = "http://localhost:8000"
                
        t = threading.Thread(target=registerForAlert,args=(url,sensorId,quietFlag,resultsFile,tb))
        t.start()
        sendPulseStream(url,sensorId,tb)
    except:
        traceback.print_exc()
        
    
    

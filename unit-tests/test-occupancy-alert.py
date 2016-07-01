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


'''
Created on Mar 9, 2015

@author: local
'''
import time
import argparse
import traceback
import requests
import socket
import ssl
from bitarray import bitarray
global secure
secure = True
from multiprocessing import Process
import urlparse
import os
import json as js
from bson.json_util import dumps
import BootstrapPythonPath
BootstrapPythonPath.setPath()


global msodConfig
msodConfig = None


def registerForAlert(serverUrl,sensorId,quiet):

    try:
        parsedUrl = urlparse.urlsplit(serverUrl)
        netloc = parsedUrl.netloc
        host = netloc.split(":")[0]
        url = serverUrl + "/sensordata/getMonitoringPort/" + sensorId
        print url
        r = requests.post(url, verify=False)
        json = r.json()
        port = json["port"]
        print "Receiving occupancy alert on port " + str(port)
        if secure:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock = ssl.wrap_socket(s)
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
                except KeyboardInterrupt:
                    break
                if alertCounter % 1000 == 0:
                    elapsedTime = time.time() - startTime
                    estimatedStorage = alertCounter * 7
                    estimatedKeyStorage = alertCounter * 4
                    totalStorage = estimatedStorage + estimatedKeyStorage
                    storagePerUnitTime = totalStorage / elapsedTime
                    if not os.path.exists("occupancy-receiver.out"):
                        fout = open("occupancy-receiver.out", "w+")
                    else:
                        fout = open("occupancy-receiver.out", "a+")
                    message = "Elapsed time " + str(elapsedTime) + " Seconds; " + " alertCounter = " + \
                     str(alertCounter) + " Storage: Data " + str(estimatedStorage) + " bytes " + \
                     " keys = " + str(estimatedKeyStorage) + " bytes " + " Total = " + str(totalStorage) + \
                     " Bytes Per Second = " + str(storagePerUnitTime)
                    fout.write(message)
                    print message
                    fout.close()

        finally:
            endTime = time.time()
            elapsedTime = endTime - startTime
            estimatedStorage = alertCounter * 7
            print "Elapsed time ", elapsedTime, " Seconds; ", " alertCounter = ", \
                     alertCounter , " Storage: Data ", estimatedStorage, " bytes"
    except:
        traceback.print_exc()
        raise

def sendStream(serverUrl, sensorId, filename):
    global secure
    url = serverUrl + "/sensordata/getStreamingPort/" + sensorId
    print url
    r = requests.post(url, verify=False)
    json = r.json()
    port = json["port"]
    print "port = ", port
    parsedUrl = urlparse.urlsplit(serverUrl)
    netloc = parsedUrl.netloc
    host = netloc.split(":")[0]
    if not secure:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock = ssl.wrap_socket(s)
        sock.connect((host, port))
    r = requests.post(serverUrl + "/sensordb/getSensorConfig/" + sensorId,verify=False)
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
    fStart = json["sensorConfig"]["thresholds"][json["sensorConfig"]["thresholds"].keys()[0]]["minFreqHz"]
    fStop = json["sensorConfig"]["thresholds"][json["sensorConfig"]["thresholds"].keys()[0]]["maxFreqHz"]

    with open(filename, "r") as f:
        headersSent = False
        while True:
            # Read and send system,loc and data message.
            if not headersSent :
                for i in range(0, 3):
                    readBuffer = ""
                    while True:
                        byte = f.read(1)
                        if byte == "\r":
                            break;
                        readBuffer = readBuffer + byte
                    bytesToRead = int(readBuffer)
                    toSend = f.read(bytesToRead)

                    headerToSend = js.loads(str(toSend))
                    headerToSend["SensorID"] = sensorId
                    if headerToSend["Type"] == "Data" :
                        headerToSend["mPar"]["tm"] = timeBetweenReadings
                        headerToSend["mPar"]["fStart"] = fStart
                        headerToSend["mPar"]["fStop"] = fStop


                    toSend = js.dumps(headerToSend, indent=4)
                    length = len(toSend)
                    # print toSend
                    sock.send(str(length) + "\n")
                    sock.send(toSend)
                    print "Header sent"
                headersSent = True
            time.sleep(timeBetweenReadings)
            toSend = f.read(56)
            sock.send(toSend)


if __name__ == "__main__":
    global secure
    try :
        parser = argparse.ArgumentParser(description="Process command line args")
        parser.add_argument("-sensorId", help="Sensor ID for which we are interested in occupancy alerts")
        parser.add_argument("-data", help="Data file")
        parser.add_argument("-quiet", help="Quiet switch", dest='quiet', action='store_true')
        parser.add_argument('-secure', help="Use HTTPS", dest='secure', action='store_true')
        parser.add_argument('-url', help='base url for server')
        parser.add_argument('-rc', help='receiver count')
        parser.add_argument('-host', help = 'host')
        parser.add_argument('-port', help = 'port')
        parser.set_defaults(quiet=False)
        parser.set_defaults(secure=True)
        parser.set_defaults(rc=1)
        args = parser.parse_args()
        sensorId = args.sensorId
        dataFile = args.data
        quietFlag = True
        sendData = dataFile != None
        quietFlag = args.quiet
        secure = args.secure
        host = args.host
        port = args.port
        if host == None:
            host = os.environ.get("MSOD_WEB_HOST")
        if port == None:
            port = "443"
        rc = int(args.rc)
        url = args.url


        if url == None:
            if secure:
                url = "https://" + host + ":" + port
            else:
                url = "http://" + host + ":" + port

        for i in range(0, rc):
            t = Process(target=registerForAlert, args=(url, sensorId, quietFlag))
            t.start()
        if sendData:
            sendStream(url, sensorId, dataFile)
        else:
            print "Not sending data"
    except:
        traceback.print_exc()




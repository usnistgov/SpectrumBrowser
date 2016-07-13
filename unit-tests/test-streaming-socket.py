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
import json as js
import os

secure = True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process command line args")
    parser.add_argument("-data", help="File name to stream")
    parser.add_argument("-sensorId", help="sensorId")
    parser.add_argument("-host",help="Server host.",default = "localhost")
    parser.add_argument("-port",help="Server port.",default = "8443")
    args = parser.parse_args()
    host = args.host
    webPort = args.port
    filename = args.data
    if filename is None:
        print "please specify -data filename"
        sys.exit()
    sensorId = args.sensorId
    if sensorId is None:
        print "Please specify sensorID"
        sys.exit()
    r = requests.post("https://"+ host + ":" + webPort + "/sensordata/getStreamingPort/" + sensorId,verify=False)
    json = r.json()
    port = json["port"]
    print "port = ", port
    print ("Sending request : " + "https://" + host + ":" + webPort +  "/sensordb/getSensorConfig/" + sensorId,)
    r = requests.post("https://" + host + ":" + webPort +  "/sensordb/getSensorConfig/" + sensorId,verify=False)
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
    if not secure:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock = ssl.wrap_socket(s)
        sock.connect((host, port))
    headersSent = False
    with open(filename, "r") as f:
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
                    headerToSend["t"] = int(time.time())
                    if headerToSend["Type"] == "Data" :
                        headerToSend["mPar"]["tm"] = timeBetweenReadings

                    toSend = js.dumps(headerToSend, indent=4)
                    length = len(toSend)
                    print toSend
                    sock.send(str(length) + "\n")
                    sock.send(toSend)
                    print "Header sent"
                headersSent = True
            time.sleep(timeBetweenReadings)
            toSend = f.read(56)
            sock.send(toSend)


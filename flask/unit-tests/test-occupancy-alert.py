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

def registerForAlert(serverUrl,sensorId,quiet):
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
                except KeyboardInterrupt:
                    break
                if alertCounter % 1000 == 0:
                    elapsedTime = time.time() - startTime
                    estimatedStorage = alertCounter * 7
                    estimatedKeyStorage = alertCounter * 4
                    totalStorage =  estimatedStorage + estimatedKeyStorage
                    storagePerUnitTime = totalStorage/elapsedTime
                    if not os.path.exists("occupancy-receiver.out"):
                        fout = open("occupancy-receiver.out","w+")
                    else:
                        fout = open("occupancy-receiver.out","a+")
                    message =  "Elapsed time " + str(elapsedTime) +  " Seconds; " + " alertCounter = " + \
                     str(alertCounter) + " Storage: Data " + str(estimatedStorage) + " bytes " + \
                     " keys = " + str(estimatedKeyStorage) + " bytes " + " Total = " + str(totalStorage) +\
                     " Bytes Per Second = " + str(storagePerUnitTime)
                    fout.write(message)
                    print message
                    fout.close()
                
        finally:
            endTime = time.time()
            elapsedTime = endTime - startTime
            estimatedStorage = alertCounter * 7
            print "Elapsed time ",elapsedTime, " Seconds; ", " alertCounter = ",\
                     alertCounter , " Storage: Data ",estimatedStorage, " bytes"
                
            
    except:
        traceback.print_exc()
        raise
    
def sendStream(serverUrl,sensorId,filename):
    global secure
    url = serverUrl + "/sensordata/getStreamingPort/" + sensorId
    print url
    r = requests.post(url,verify=False)
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

    with open(filename,"r") as f:
        while True:
            toSend = f.read(56)
            sock.send(toSend)
            time.sleep(.0001)


if __name__== "__main__":
    global secure
    try :
        parser = argparse.ArgumentParser(description="Process command line args")
        parser.add_argument("-sensorId",help="Sensor ID for which we are interested in occupancy alerts")
        parser.add_argument("-data",help="Data file")
        parser.add_argument("-quiet", help="Quiet switch", dest='quiet', action='store_true')
        parser.add_argument('-secure', help="Use HTTPS", dest= 'secure', action='store_true')
        parser.add_argument('-url', help='base url for server')
        parser.set_defaults(quiet=False)
        parser.set_defaults(secure=True)
        args = parser.parse_args()
        sensorId = args.sensorId
        dataFile = args.data
        quietFlag = True
        sendData = dataFile != None
        quietFlag = args.quiet
        secure = args.secure
        url = args.url
            
       
        if url == None:     
            if secure:
                url= "https://localhost:8443"
            else:
                url = "http://localhost:8000"
                
        t = Process(target=registerForAlert,args=(url,sensorId,quietFlag))
        t.start()
        if sendData:
            sendStream(url,sensorId,dataFile)
        else:
            print "Not sending data"
    except:
        traceback.print_exc()
        
    
    

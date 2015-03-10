'''
Created on Mar 9, 2015

@author: local
'''
import sys
import time
import zmq
import argparse
import traceback
import requests
import socket
import ssl
from bson.json_util import loads,dumps
from bitarray import bitarray


if __name__== "__main__":
    try :
        parser = argparse.ArgumentParser(description="Process command line args")
        parser.add_argument("-sensorId",help="Sensor ID for which we are interested in occupancy alerts")
        args = parser.parse_args()
        sensorId = args.sensorId
        url = "http://localhost:8000/sensordata/getMonitoringPort/" + sensorId
        print url
        r = requests.post(url)
        json = r.json()
        port = json["port"]
        print "Receiving occupancy alert on port " + str(port)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock = ssl.wrap_socket(s, ca_certs="dummy.crt",cert_reqs=ssl.CERT_OPTIONAL)
        sock.connect(('localhost', port))
        request = {"SensorID":sensorId}
        req = dumps(request)
        sock.send(req)
        while True:
            occupancy = sock.recv()
            a = bitarray(endian="big")
            a.frombytes(occupancy)
            print a

    except:
        traceback.print_exc()
        
    
    

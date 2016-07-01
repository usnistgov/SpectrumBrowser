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


import unittest
import json
import requests
import argparse
import os
import socket
import ssl
import time


class  DisconnectTest(unittest.TestCase):
    def setUp(self ):
        self.sensorId = "E6R16W5XS"

    def testDisconnectSensor(self):
        params = {}
        params["agentName"] = "NIST_ESC"
        params["key"] = "ESC_PASS"
        r = requests.post("https://"+ host + ":" + str(443) + "/sensorcontrol/disconnectSensor/" + self.sensorId, data=json.dumps(params),verify=False)
	print "statusCode ", str(r.status_code)
	self.assertTrue(r.status_code == 200)
	resp1 = r.json()
	print json.dumps(resp1,indent=3)
	self.assertTrue(resp1["status"] == "OK")
	


    def tearDown(self):
	print "tearDown"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process command line args")
    parser.add_argument("-host",help="Server host.")
    parser.add_argument("-port",help="Server port.")
    args = parser.parse_args()
    global host
    global webPort
    host = args.host
    if host == None:
        host = os.environ.get("MSOD_WEB_HOST")
    webPort = args.port
    if webPort == None:
        webPort = "443"

    if host == None or webPort == None:
        print "Require host and web port"
    webPortInt = int(webPort)
    if webPortInt < 0 :
        print "Invalid params"
        os._exit()
    suite = unittest.TestLoader().loadTestsFromTestCase(DisconnectTest)
    unittest.TextTestRunner(verbosity=2).run(suite)

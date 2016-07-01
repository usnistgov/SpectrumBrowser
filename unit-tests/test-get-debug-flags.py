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

class  TestGetDebugFlags(unittest.TestCase):

    def setUp(self ):
        params = {}
        params["emailAddress"] = "admin@nist.gov"
        params["password"] = "Administrator12!"
        params["privilege"] = "admin"
        r = requests.post("https://"+ host + ":" + webPort + "/admin/authenticate" , data = json.dumps(params), verify=False)
        resp = r.json()
        print json.dumps(resp,indent=4)
        self.token = resp["sessionId"]

    def testGetSetDebugFlags(self):
        r = requests.post("https://"+ host + ":" + webPort + "/svc/getDebugFlags/" + self.token , verify=False)
	print "status code " , r.status_code
        resp = r.json()
        print json.dumps(resp,indent=4)
	resp["debugFlags"]["MSOD_DISABLE_AUTH"] = True
        r = requests.post("https://"+ host + ":" + webPort + "/svc/setDebugFlags/" + self.token , data = json.dumps(resp["debugFlags"]), verify=False)
	self.assertTrue(r.status_code == 200)
	resp1 = r.json()
        r = requests.post("https://"+ host + ":" + webPort + "/svc/getDebugFlags/" + self.token , verify=False)
        resp2 = r.json()
	self.assertTrue(resp2["status"] == "OK")
	self.assertTrue(resp["debugFlags"]["MSOD_DISABLE_AUTH"] == resp2["debugFlags"]["MSOD_DISABLE_AUTH"])

    def tearDown(self):
        r = requests.post("https://"+ host + ":" + webPort + "/admin/logOut/"  + self.token, verify=False)

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
        webPort = "8443"

    if host == None or webPort == None:
        print "Require host and web port"
    webPortInt = int(webPort)
    if webPortInt < 0 :
        print "Invalid params"
        os._exit()
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGetDebugFlags)
    unittest.TextTestRunner(verbosity=2).run(suite)


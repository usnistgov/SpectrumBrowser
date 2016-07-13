#! /usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
# This software was developed by employees of the National Institute of
# Standards and Technology (NIST), and others.
# This software has been contributed to the public domain.
# Pursuant to title 15 Untied States Code Section 105, works of NIST
# employees are not subject to copyright protection in the United States
# and are considered to be in the public domain.
# As a result, a formal license is not needed to use this software.
#
# This software is provided "AS IS."
# NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
# OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
# AND DATA ACCURACY.  NIST does not warrant or make any representations
# regarding the use of the software or the results thereof, including but
# not limited to the correctness, accuracy, reliability or usefulness of
# this software.


import unittest
import json
import requests
import argparse
import os
import time


class GetCaptureEventTest(unittest.TestCase):
    def setUp(self):
        global sensorId
        global webPort
        self.sensorId = sensorId
        params = {}
        params["emailAddress"] = "admin@nist.gov"
        params["password"] = "Administrator12!"
        params["privilege"] = "admin"
        url = "https://"+ host + ":" + str(8443) + "/admin/authenticate"
        print "url = ", url
        r = requests.post(url, data = json.dumps(params), verify=False)
        resp = r.json()
        print json.dumps(resp,indent=4)
        self.token = resp["sessionId"]
        url = "https://" + str(host) + ":" + str(443)
        r = requests.post(url + "/spectrumbrowser/isAuthenticationRequired", verify=False)
        jsonresp = r.json()
        print json
        self.assertTrue(not jsonresp["AuthenticationRequired"])
        self.sessionToken = jsonresp["SessionToken"]

#    def testDeleteEvents(self):
#        url = "https://" + host + ":" + str(443) + "/eventstream/deleteCaptureEvents/" + sensorId + "/0/"  + self.token
#        r = requests.post(url,verify=False)
#	print "Status_code = ", r.status_code
#	self.assertTrue(r.status_code==200)

#    def testArmSensor(self):
#        params = {}
#        params["agentName"] = "NIST_ESC"
#        params["key"] = "ESC_PASS"
#        print "https://"+ host + ":" + str(443) + "/sensorcontrol/armSensor/" + self.sensorId
#        r = requests.post("https://"+ host + ":" + str(443) + "/sensorcontrol/armSensor/" + self.sensorId, data=json.dumps(params),verify=False)
#        print r.status_code
#        self.assertTrue(r.status_code == 200)
#        resp = r.json()
#        self.assertTrue(resp["status"] == "OK")

    def testRunForensics(self):
        url = "https://"+ host + ":" + str(443) + "/eventstream/getCaptureEvents/" + self.sensorId + "/0/" + str(int(time.time())) + "/" + self.sessionToken
        print url
        r = requests.post(url, verify=False)
        resp = r.json()
        print json.dumps(resp, indent=4)
        self.assertTrue(r.status_code == 200)
        self.assertTrue(resp["status"] == "OK")
        self.assertTrue("events" in resp)
        if len(resp["events"]) > 0:
            timeStamp = resp["events"][0]["t"]
        else:
            print "No events found"
            os._exit(0)
        url = "https://"+ host + ":" + str(443) + "/sensorcontrol/runForensics/" + self.sensorId + "/dummy/" + str(timeStamp) + "/" + self.sessionToken
        r = requests.post(url, verify=False)
        print "status_code = ", r.status_code
        self.assertTrue(r.status_code == 200)
        resp = r.json()
        print json.dumps(resp, indent=4)

    def tearDown(self):
        r = requests.post("https://"+ host + ":" + str(8443) + "/admin/logOut/"  + self.token, verify=False)
        print "tearDown"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process command line args")
    parser.add_argument("-host", help="Server host.")
    parser.add_argument("-port", help="Server port.")
    parser.add_argument("-sensorId", help="Sensor ID.", default="E6R16W5XS")
    args = parser.parse_args()
    global host
    global webPort
    global sensorId
    host = args.host
    sensorId = args.sensorId

    if host is None:
        host = os.environ.get("MSOD_WEB_HOST")
    webPort = args.port
    if webPort is None:
        webPort = "443"

    if host is None or webPort is None:
        print "Require host and web port"
    webPortInt = int(webPort)
    if webPortInt < 0:
        print "Invalid params"
        os._exit()
    suite = unittest.TestLoader().loadTestsFromTestCase(GetCaptureEventTest)
    unittest.TextTestRunner(verbosity=2).run(suite)

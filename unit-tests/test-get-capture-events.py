
import unittest
import json
import requests
import argparse
import os
import socket
import ssl
import time


class  GetCaptureEventTest(unittest.TestCase):
    def setUp(self ):
	global sensorId
	self.sensorId = sensorId
        params = {}
        params["agentName"] = "NIST_ESC"
        params["key"] = "ESC_PASS"
        r = requests.post("https://"+ host + ":" + str(443) + "/sensorcontrol/armSensor/" + self.sensorId, data=json.dumps(params),verify=False)
        self.assertTrue(r.status_code == 200)
        resp = r.json()
        self.assertTrue(resp["status"] == "OK")
	self.url = "https://" + str(host) + ":" + str(443)
    	r = requests.post(self.url + "/spectrumbrowser/isAuthenticationRequired",verify=False)
    	jsonresp = r.json()
	print json
	self.assertTrue(not jsonresp["AuthenticationRequired"])
    	self.sessionToken = jsonresp["SessionToken"]

    def testGetCaptureEvents(self):
	# give time for "arm processing"
	time.sleep(1)
        params = {}
	url = "https://"+ host + ":" + str(443) + "/spectrumbrowser/getCaptureEvents/" + self.sensorId + "/0/0/" + self.sessionToken
	print url
        r = requests.post(url,verify=False)

        resp = r.json()
	print json.dumps(resp,indent=4)
        self.assertTrue(r.status_code == 200)
        self.assertTrue(resp["status"] == "OK")
	self.assertTrue("events" in resp)

    def tearDown(self):
	print "tearDown"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process command line args")
    parser.add_argument("-host",help="Server host.")
    parser.add_argument("-port",help="Server port.")
    parser.add_argument("-sensorId",help="NistUSRPSensor1")
    args = parser.parse_args()
    global host
    global webPort
    global sensorId
    host = args.host
    sensorId = args.sensorId
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
    suite = unittest.TestLoader().loadTestsFromTestCase(GetCaptureEventTest)
    unittest.TextTestRunner(verbosity=2).run(suite)

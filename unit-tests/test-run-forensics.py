
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
	global webPort
        self.sensorId = sensorId
	params = {}
        params["emailAddress"] = "admin@nist.gov"
        params["password"] = "Administrator12!"
        params["privilege"] = "admin"
	url = "https://"+ host + ":" + str(8443) + "/admin/authenticate"
	print "url = " , url
        r = requests.post(url, data = json.dumps(params), verify=False)
        resp = r.json()
        print json.dumps(resp,indent=4)
	self.token = resp["sessionId"]
	url = "https://" + str(host) + ":" + str(443)
    	r = requests.post(url + "/spectrumbrowser/isAuthenticationRequired",verify=False)
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
#	 print r.status_code
#        self.assertTrue(r.status_code == 200)
#        resp = r.json()
#        self.assertTrue(resp["status"] == "OK")

    def testGetCaptureEvents(self):
	# give time for "arm processing"
	global timeStamp
	time.sleep(1)
        params = {}
	url = "https://"+ host + ":" + str(443) + "/spectrumbrowser/getCaptureEvents/" + self.sensorId + "/0/" + str(int(time.time())) + "/" + self.sessionToken
	print url
        r = requests.post(url,verify=False)
        resp = r.json()
	print json.dumps(resp,indent=4)
	timeStamp = resp["events"][0]["t"]
        self.assertTrue(r.status_code == 200)
        self.assertTrue(resp["status"] == "OK")
	self.assertTrue("events" in resp)

    def testRunForensics(self):
	global timeStamp
	url = "https://"+ host + ":" + str(443) + "/sensorcontrol/runForensics/" + self.sensorId + "/dummy/" + str(timeStamp) + "/" + self.sessionToken
        r = requests.post(url,verify=False)
	print "status_code = ",r.status_code
	self.assertTrue(r.status_code == 200)
        resp = r.json()
	print json.dumps(resp,indent=4)

    def tearDown(self):
        r = requests.post("https://"+ host + ":" + str(8443) + "/admin/logOut/"  + self.token, verify=False)
	print "tearDown"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process command line args")
    parser.add_argument("-host",help="Server host.")
    parser.add_argument("-port",help="Server port.")
    parser.add_argument("-sensorId",help="Sensor ID.",default="E6R16W5XS")
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

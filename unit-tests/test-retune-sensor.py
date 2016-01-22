import unittest
import json
import requests
import argparse
import os
import socket
import ssl
import time


class  ArmTest(unittest.TestCase):
    def setUp(self ):
        self.sensorId = "E6R16W5XS"

    def testRetuneSensor(self):
        params = {}
        params["agentName"] = "NIST_ESC"
        params["key"] = "ESC_PASS"
        r = requests.post("https://"+host + ":" + str(443) + "/sensordb/getSensorConfig/" + self.sensorId,verify=False)
	resp = r.json()
	sensorConfig = resp["sensorConfig"]
	bandNames = sensorConfig["thresholds"].keys()
	print str(bandNames)
	while True:
	   for band in bandNames:
		print "RETUNING TO " + band
           	r = requests.post("https://"+ host + ":" + str(443) + "/sensorcontrol/retuneSensor/" + self.sensorId + "/" + band, data=json.dumps(params),verify=False)
		print "statusCode ", str(r.status_code)
	   	self.assertTrue(r.status_code == 200)
	   	resp1 = r.json()
	   	print json.dumps(resp1,indent=3)
	   	self.assertTrue(resp1["status"] == "OK")
	   	r = requests.post("https://"+host + ":" + str(443) + "/sensordb/getSensorConfig/" + self.sensorId,verify=False)
	   	resp = r.json()
	   	self.assertTrue(resp["status"] == "OK")
	   	sensorConfig = resp["sensorConfig"]
	   	bands = sensorConfig["thresholds"]
	   	self.assertTrue(band in bands)
	   	self.assertTrue(bands[band]["active"] == True)
	   	for bandElement in bands.values():
			if bandElement['active'] :
				self.assertTrue(bands[band] == bandElement)
	   	time.sleep(20)
	


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
    suite = unittest.TestLoader().loadTestsFromTestCase(ArmTest)
    unittest.TextTestRunner(verbosity=2).run(suite)

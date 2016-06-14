import unittest
import json
import requests
import argparse
import os
import json

class  SensorConfigTest(unittest.TestCase):
    def setUp(self):
        global host
        global webPort
        self.sensorId = "SensorSim1"
	self.serverUrlPrefix = "https://" + host + ":" + str(webPort)

    def test_get_sensor_config(self):
        r = requests.post(self.serverUrlPrefix + "/sensordb/getSensorConfig/" + self.sensorId,verify=False)
        jsonVal = r.json()
        print json.dumps(jsonVal, indent=4)
        self.assertTrue(json != None)
        self.assertTrue(jsonVal["sensorConfig"]["SensorID"] == self.sensorId)
	activeBands = jsonVal["sensorConfig"]["thresholds"]
	for band in activeBands.values():
		if band["active"]:
			print "Active Band:"
			print json.dumps(band, indent = 4)

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
    suite = unittest.TestLoader().loadTestsFromTestCase(SensorConfigTest)
    unittest.TextTestRunner(verbosity=2).run(suite)

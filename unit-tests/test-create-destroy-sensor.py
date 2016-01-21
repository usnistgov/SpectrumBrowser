import unittest
import json
import requests
import argparse
import os


class  TestCreateDestroySensor(unittest.TestCase):
    def setUp(self ):
        params = {}
        params["emailAddress"] = "admin@nist.gov"
        params["password"] = "Administrator12!"
        params["privilege"] = "admin"
        r = requests.post("https://"+ host + ":" + str(webPort) + "/admin/authenticate" , data = json.dumps(params), verify=False)
        resp = r.json()
        print json.dumps(resp,indent=4)
        self.token = resp["sessionId"]
	self.sensorId = "NorfolkTest"

    def testCreateDestroySensor(self):
	sensorConfig = json.load(open("NorfolkTest.config.json"))
	url = "https://" + host + ":" + str(webPort) + "/admin/addSensor/" + self.token
	r = requests.post(url, data = json.dumps(sensorConfig), verify = False)
	self.assertTrue(r.status_code == 200 )
	retval = r.json()
	sensors = retval["sensors"]
	print json.dumps(retval, indent=4)
	sensorFound = False
	for sensor in sensors:
	    if sensor["SensorID"] == self.sensorId:
		sensorFound = True	
	self.assertTrue(sensorFound)
	url = "https://" + host + ":" + str(webPort) + "/admin/purgeSensor/" + self.sensorId + "/" + self.token
	r = requests.post(url,  verify = False)
	retval = r.json()
	sensors = retval["sensors"]
	sensorFound = False
	for sensor in sensors:
	    if sensor["SensorID"] == self.sensorId:
		sensorFound = True	
	self.assertTrue(not sensorFound)
	
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
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCreateDestroySensor)
    unittest.TextTestRunner(verbosity=2).run(suite)

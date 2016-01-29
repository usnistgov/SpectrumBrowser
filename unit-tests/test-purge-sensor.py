import unittest
import json
import requests
import argparse
import os
class  TestPurgeSensor(unittest.TestCase):

    def setUp(self):
	self.sensorId = "Norfolk"
        params = {}
        params["emailAddress"] = "admin@nist.gov"
        params["password"] = "Administrator12!"
        params["privilege"] = "admin"
        r = requests.post("https://"+ host + ":" + webPort + "/admin/authenticate" , data = json.dumps(params), verify=False)
        resp = r.json()
        print json.dumps(resp,indent=4)
        self.token = resp["sessionId"]
	sensorConfig = json.load(open("TestSensor.config.json"))
        r = requests.post("https://"+ host + ":" + webPort + "/admin/addSensor" , data = json.dumps(sensorConfig), verify=False)
	

    def testPurgeSensor(self):
        r = requests.post("https://" + host + ":" + webPort + "/admin/purgeSensor/" + self.sensorId + "/" + self.token, verify=False)
        resp = r.json()
        print json.dumps(resp,indent=4)
	for sensor in resp['sensors']:
		self.assertTrue(self.sensorId != sensor['SensorID'])


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
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPurgeSensor)
    unittest.TextTestRunner(verbosity=2).run(suite)

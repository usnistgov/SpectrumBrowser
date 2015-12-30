import unittest
import json
import requests
import argparse
import os
import socket
import ssl


class  ArmTest(unittest.TestCase):
    def setUp(self ):
        self.sensorId = "E6R16W5XS"

    def testArmSensor(self):
        params = {}
        params["escName"] = "NIST_ESC"
        params["password"] = "ESC_PASS"
        r = requests.post("https://"+ host + ":" + str(443) + "/sensorcontrol/armSensor/" + self.sensorId, data=json.dumps(params),verify=False)
	print "status code " , r.status_code
	self.assertTrue(r.status_code == 200)
        resp = r.json()
	print json.dumps(resp,indent=4)
	self.assertTrue(resp["status"] == "OK")

    #def testDisarmSensor(self):
    #    r = requests.post("https://"+ host + ":" + webPort + str(443) + "/sensorcontrol/disarmSensor/" + self.sensorId + "/" + self.token,verify=False)
    #    resp = r.json()
    #    self.assertTrue(r.status_code == 200)
    #    self.assertTrue(resp["status"] == "OK")

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

import unittest
import json
import requests
import argparse
import os

class  TestCheckSessionTimeout(unittest.TestCase):
    def setUp(self):
	global host
	global webPort
	self.url = "https://" + str(host) + ":" + str(webPort)
    	r = requests.post(self.url + "/spectrumbrowser/isAuthenticationRequired",verify=False)
    	json = r.json()
	print json
    	if json["AuthenticationRequired"] :
        	print ("please disable authentication on the server and configure sensor for streaming")
        	sys.exit()
    	self.sessionToken = json["SessionToken"]

	
    def test_session_timer(self):
        global host
        global webPort
	global sensorId
	url=self.url + "/spectrumbrowser/checkSessionTimeout/"  + self.sessionToken
	r = requests.post(url,verify=False)
	js = r.json()
	self.assertTrue(js["status"] == "OK")

    def tearDown(self):
        r = requests.post(self.url + "/spectrumbrowser/logout/" + self.sessionToken,verify=False)

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
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCheckSessionTimeout)
    unittest.TextTestRunner(verbosity=2).run(suite)

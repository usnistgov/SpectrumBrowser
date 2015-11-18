import unittest
import json
import requests
import argparse

class  TestGetLastAcquisitionTimestamp(unittest.TestCase):
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

	
    def test_get_last_acquisition_timestamp(self):
        global host
        global webPort
	global sensorId
	url=self.url + "/spectrumbrowser/getLastSensorAcquisitionTimeStamp/" + sensorId + "/" + self.sessionToken
	r = requests.post(url,verify=False)
	json = r.json()
	print json
	self.assertTrue(json["aquisitionTimeStamp"] > 0)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process command line args")
    parser.add_argument("-host",help="Server host.")
    parser.add_argument("-port",help="Server port.")
    parser.add_argument("-sensorId",help="Sensor ID")
    args = parser.parse_args()
    global host
    global webPort
    global sensorId
    host = args.host
    if host == None:
        host = os.environ.get("MSOD_WEB_HOST")
    webPort = args.port
    if webPort == None:
       webPort = "443"

    sensorId = args.sensorId

    if host == None or webPort == None:
        print "Require host and web port"
    webPortInt = int(webPort)
    if webPortInt < 0 :
        print "Invalid params"
        os._exit()
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGetLastAcquisitionTimestamp)
    unittest.TextTestRunner(verbosity=2).run(suite)

import unittest
import json
import requests
import argparse
import os
import time

class  TestPostEvent(unittest.TestCase):
   def loginAsAdmin(self):
        params = {}
        params["emailAddress"] = "admin@nist.gov"
        params["password"] = "Administrator12!"
        params["privilege"] = "admin"
        r = requests.post("https://"+ host + ":" + str(8443) + "/admin/authenticate" , data = json.dumps(params), verify=False)
        resp = r.json()
        token = resp["sessionId"]
	return token

   def setUp(self):
	self.adminToken = self.loginAsAdmin()
	sensorConfig = json.load(open("TestSensor.config.json"))
	url = "https://" + host + ":" + str(8443) + "/admin/addSensor/" + self.adminToken
	r = requests.post(url, data = json.dumps(sensorConfig), verify = False)
	self.assertTrue(r.status_code == 200 )


	self.dataToPost = json.load(open("sensor.event"))
	self.t = int(time.time())
	self.t = self.dataToPost["t"]
	self.sensorId = self.dataToPost["SensorID"]
	self.url = "https://" + host + ":" + str(443)
    	r = requests.post(self.url + "/spectrumbrowser/isAuthenticationRequired",verify=False)
    	jsonVal = r.json()
	print jsonVal
    	if jsonVal["AuthenticationRequired"] :
        	print ("please disable authentication on the server")
        	sys.exit()
    	self.sessionToken = jsonVal["SessionToken"]

   def testPostEvent(self):
	url = self.url + "/eventstream/postCaptureEvent"
	r = requests.post(url,data=json.dumps(self.dataToPost,indent=4),verify=False)
	print "status code ", r.status_code
	url = self.url + "/eventstream/getCaptureEvents/"+self.sensorId+ "/" + str(self.t) + "/" + str(1) + "/" + self.sessionToken
	r = requests.post(url,verify=False)
	print "status code ", r.status_code
	self.assertTrue(r.status_code == 200)
	print r.json()

   def tearDown(self):
	url = "https://" + host + ":" + str(8443) + "/admin/purgeSensor/" + self.sensorId + "/" + self.adminToken
	r = requests.post(url,  verify = False)
        r = requests.post("https://"+ host + ":" + str(8443) + "/admin/logOut/" + self.adminToken, verify=False)
	self.assertTrue(r.status_code == 200 )



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process command line args")
    parser.add_argument("-host",help="Server host.")
    parser.add_argument("-file",help="Data file.")
    args = parser.parse_args()
    global filename
    global host
    host = args.host
    if host == None:
        host = os.environ.get("MSOD_WEB_HOST")

    if host == None :
        print "Require host and web port"
        os._exit()

    filename = args.file
    if filename == None:
	filename = "NorfolkTestSample.txt"

    if not os.path.exists(filename):
        print "Require data file -file argument."
        os._exit()
	
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPostEvent)
    unittest.TextTestRunner(verbosity=2).run(suite)

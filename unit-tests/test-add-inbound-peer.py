import unittest
import json
import requests
import argparse
import os

class  TestAddInboundPeer(unittest.TestCase):

    def setUp(self ):
        params = {}
        params["emailAddress"] = "admin@nist.gov"
        params["password"] = "Administrator12!"
        params["privilege"] = "admin"
        r = requests.post("https://"+ host + ":" + webPort + "/admin/authenticate" , data = json.dumps(params), verify=False)
        resp = r.json()
        print json.dumps(resp,indent=4)
        self.token = resp["sessionId"]


    def testAddInboundPeer(self):
	peerConfig = {}
	peerConfig["comment"] =  ""
        peerConfig["PeerId"] =  "foo"
        peerConfig["key"] =  "bar"
        r = requests.post("https://"+ host + ":" + webPort + "/admin/addInboundPeer/" + self.token , data = json.dumps(peerConfig), verify=False)
	print json.dumps(r.json())

    def tearDown( self ) :
        r = requests.post("https://"+ host + ":" + webPort + "/admin/deleteInboundPeer/foo/" + self.token , verify=False)
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
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddInboundPeer)
    unittest.TextTestRunner(verbosity=2).run(suite)

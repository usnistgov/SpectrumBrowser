import unittest
import requests
import argparse
from websocket import create_connection
import json
import os
import ssl


class TestResourceStreaming(unittest.TestCase):

    def setUp(self):
        params = {}
        params["emailAddress"] = "admin@nist.gov"
        params["password"] = "Administrator12!"
        params["privilege"] = "admin"
        print "host = ", host , "webPort = ",webPort
        r = requests.post("https://"+ host + ":" + webPort + "/admin/authenticate" , data = json.dumps(params), verify=False)
        resp = r.json()
        print json.dumps(resp,indent=4)
        self.assertTrue("sessionId" in resp)
        self.token = resp["sessionId"]

    def tearDown(self):
        if self.ws != None:
            self.ws.close()
        if self.token != None:
            r = requests.post("https://"+ host + ":" + webPort + "/admin/logOut/" + self.token, verify=False)
        print "Done"

    def test_establish_resource_websocket(self):
        global host
        global webPort
        self.ws = create_connection("wss://" + host + ":" + webPort +  "/admin/sysmonitor", sslopt=dict(cert_reqs=ssl.CERT_NONE))
        self.ws.send(self.token)
        data = self.ws.recv()
        resources = json.loads(data)
        print json.dumps(resources,indent=4)
        self.assertTrue(resources["CPU"] >= 0 )
        self.assertTrue(resources["NetSent"] >= 0  )
        self.assertTrue(resources["NetRecv"] >= 0  )
        self.assertTrue(resources["Disk"] >= 0  )


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
    suite = unittest.TestLoader().loadTestsFromTestCase(TestResourceStreaming)
    unittest.TextTestRunner(verbosity=2).run(suite)


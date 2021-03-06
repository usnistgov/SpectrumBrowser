#! /usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
#This software was developed by employees of the National Institute of
#Standards and Technology (NIST), and others.
#This software has been contributed to the public domain.
#Pursuant to title 15 Untied States Code Section 105, works of NIST
#employees are not subject to copyright protection in the United States
#and are considered to be in the public domain.
#As a result, a formal license is not needed to use this software.
#
#This software is provided "AS IS."
#NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
#OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
#MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
#AND DATA ACCURACY.  NIST does not warrant or make any representations
#regarding the use of the software or the results thereof, including but
#not limited to the correctness, accuracy, reliability or usefulness of
#this software.

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
        print "host = ", host, "webPort = ", webPort
        r = requests.post(
            "https://" + host + ":" + webPort + "/admin/authenticate",
            data=json.dumps(params),
            verify=False)
        resp = r.json()
        print json.dumps(resp, indent=4)
        self.assertTrue("sessionId" in resp)
        self.token = resp["sessionId"]

    def tearDown(self):
        if self.ws is not None:
            self.ws.close()
        if self.token is not None:
            r = requests.post("https://" + host + ":" + webPort +
                              "/admin/logOut/" + self.token,
                              verify=False)
        print "Done"

    def test_establish_resource_websocket(self):
        global host
        global webPort
        self.ws = create_connection(
            "wss://" + host + ":" + webPort + "/admin/sysmonitor",
            sslopt=dict(cert_reqs=ssl.CERT_NONE))
        self.ws.send(self.token)
        data = self.ws.recv()
        resources = json.loads(data)
        print json.dumps(resources, indent=4)
        self.assertTrue(resources["CPU"] >= 0)
        self.assertTrue(resources["NetSent"] >= 0)
        self.assertTrue(resources["NetRecv"] >= 0)
        self.assertTrue(resources["Disk"] >= 0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process command line args")
    parser.add_argument("-host", help="Server host.")
    parser.add_argument("-port", help="Server port.")
    args = parser.parse_args()
    global host
    global webPort
    host = args.host
    if host is None:
        host = os.environ.get("MSOD_WEB_HOST")
    webPort = args.port
    if webPort is None:
        webPort = "8443"

    if host is None or webPort is None:
        print "Require host and web port"
    webPortInt = int(webPort)
    if webPortInt < 0:
        print "Invalid params"
        os._exit()
    suite = unittest.TestLoader().loadTestsFromTestCase(TestResourceStreaming)
    unittest.TextTestRunner(verbosity=2).run(suite)

#! /usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
# This software was developed by employees of the National Institute of
# Standards and Technology (NIST), and others.
# This software has been contributed to the public domain.
# Pursuant to title 15 Untied States Code Section 105, works of NIST
# employees are not subject to copyright protection in the United States
# and are considered to be in the public domain.
# As a result, a formal license is not needed to use this software.
#
# This software is provided "AS IS."
# NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
# OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
# AND DATA ACCURACY.  NIST does not warrant or make any representations
# regarding the use of the software or the results thereof, including but
# not limited to the correctness, accuracy, reliability or usefulness of
# this software.

import unittest
import json
import requests
import argparse
import os
import time


class TestGetSensorsByFrequencyBand(unittest.TestCase):
    def setUp(self):
        self.url = "https://" + str(host) + ":" + str(443)
        r = requests.post(
            self.url + "/spectrumbrowser/isAuthenticationRequired",
            verify=False)
        jsonresp = r.json()
        print json
        self.assertTrue(not jsonresp["AuthenticationRequired"])
        self.sessionToken = jsonresp["SessionToken"]

    def testGetFrequencyBands(self):
        r = requests.post(
            self.url + "/spectrumbrowser/getSensorsByFrequencyBand/Radar-SPN43/3450500000/3649500000/" + self.sessionToken ,
            verify=False)
        print "status code ", r.status_code
        self.assertTrue(r.status_code == 200)
	print r.json()
        self.assertTrue(len(r.json()["sensorIds"]) > 0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process command line args")
    parser.add_argument("-host", help="Server host.")
    parser.add_argument("-port", help="Server port.")
    parser.add_argument("-sensorId", help="Sensor ID")
    args = parser.parse_args()
    global host
    global webPort
    global sensorId
    host = args.host
    if host is None:
        host = os.environ.get("MSOD_WEB_HOST")
    webPort = args.port
    if webPort is None:
        webPort = "443"


    if host is None or webPort is None:
        print "Require host and web port"
    webPortInt = int(webPort)
    if webPortInt < 0:
        print "Invalid params"
        os._exit()
    suite = unittest.TestLoader().loadTestsFromTestCase(
        TestGetSensorsByFrequencyBand)
    unittest.TextTestRunner(verbosity=2).run(suite)

   

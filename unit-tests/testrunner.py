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
'''
Created on Mar 16, 2015

@author: local
'''
import requests
import argparse
import sys
import os
import json
import traceback
import threading
import time


def runTest(fileName):
    scriptFile = open(fileName, "r")
    tests = scriptFile.read()
    script = "[" + tests + "]"
    scripts = json.loads(script)
    startTime = time.time()
    try:
        for script in scripts:
            httpMethod = script["httpRequestMethod"]
            if httpMethod == "POST":
                print "Testing " + script["testedFunction"]
                if "requestBody" in script:
                    body = script["requestBody"]
                else:
                    body = None
                if body is None:
                    response = requests.post(script["requestUrl"],
                                             verify=False)
                else:
                    response = requests.post(script["requestUrl"],
                                             verify=False)
                responseJson = response.json()
                if response.status_code != script["statusCode"]:
                    print "Failed test -- status code did not match"
                    os.exit()

                if json.loads(script["expectedResponse"]) != responseJson:
                    print "Response did not match -- test failed."
                else:
                    print "Passed!"
            else:
                response = requests.get(script["requestUrl"])
                if response.status_code != 200:
                    print "Failed GET on URL " + script["requestUrl"]
    except:
        traceback.print_exc()
        print "Failed test suite."
    finally:
        endTime = time.time()
        delta = endTime - startTime
        print "Running time = " + str(delta) + " s."


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('-f', help='Json script')
        parser.add_argument("-u", help="base url")
        parser.add_argument("-n", help="Number of threads")
        args = parser.parse_args()
        fileName = args.f
        baseUrl = args.u
        threadCountStr = args.n
        if threadCountStr is None:
            threadCount = 1
        else:
            threadCount = int(threadCountStr)
        if baseUrl is None:
            baseUrl = "http://localhost:8000"
        if fileName is None:
            parser.error("FileName for test script missing!")
            os.exit()
        response = requests.post(baseUrl + "/getDebugFlags")
        responseObj = response.json()
        if not responseObj["disableSessionIdCheck"]:
            print "Please start gunicorn with sh start-gunicorn-run-testcases.sh"
            sys.exit()
        if responseObj["generateTestCase"]:
            print "Please start gunicorn with sh start-gunicorn-run-testcases.sh"
            sys.exit()
        print "Please load the db using the appropriate data files before starting this test."
        print str(fileName)
        for i in range(0, threadCount):
            t = threading.Thread(name="tester-thread-" + str(i),
                                 target=runTest,
                                 args=(fileName, ))
            t.start()
    except:
        traceback.print_exc()

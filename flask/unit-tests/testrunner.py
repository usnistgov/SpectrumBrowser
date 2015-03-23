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
import ssl
import time

def runTest(fileName):
    scriptFile = open(fileName,"r")
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
                if body == None:
                    response = requests.post(script["requestUrl"],verify=False)
                else:
                    response = requests.post(script["requestUrl"],verify=False)
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
                    print "Failed GET on URL " + requestUrl
    except:
        traceback.print_exc()
        print "Failed test suite."
    finally:
        endTime = time.time()
        delta = endTime - startTime
        print "Running time = " + str(delta) + " s."
                
if __name__ == "__main__":
    try :
        parser = argparse.ArgumentParser()
        parser.add_argument('-f',help='Json script')
        parser.add_argument("-u", help="base url")
        parser.add_argument("-n", help="Number of threads")
        args = parser.parse_args()
        fileName = args.f
        baseUrl = args.u
        threadCountStr = args.n
        if threadCountStr == None:
            threadCount = 1
        else:
            threadCount = int(threadCountStr)
        if baseUrl == None:
            baseUrl = "http://localhost:8000"
        if fileName == None:
            parser.error("FileName for test script missing!")
            os.exit()
        response = requests.post(baseUrl + "/getDebugFlags")
        responseObj = response.json()
        if not responseObj["disableSessionIdCheck"] :
            print "Please start gunicorn with sh start-gunicorn-run-testcases.sh"
            sys.exit()
        if responseObj["generateTestCase"]:
            print "Please start gunicorn with sh start-gunicorn-run-testcases.sh"
            sys.exit()
        print "Please load the db using the appropriate data files before starting this test."
        for i in range(0,threadCount):
            t = threading.Thread(name="tester-thread-"+str(i),target=runTest,args=(fileName,))
            t.start()
    except:
        traceback.print_exc()
            
    
            
        
    
    
    
    
    
    

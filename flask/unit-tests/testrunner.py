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
if __name__ == "__main__":
    try :
        parser = argparse.ArgumentParser()
        parser.add_argument('-f',help='Json script')
        parser.add_argument("-u", help="base url")
        args = parser.parse_args()
        fileName = args.f
        baseUrl = args.u
        if baseUrl == None:
            baseUrl = "http://localhost:8000"
        if fileName == None:
            parser.error("FileName for test script missing!")
            os.exit()
        response = requests.post(baseUrl + "/getDebugFlags")
        responseObj = response.json()
        if not responseObj["disableSessionIdCheck"] :
            print "Please edit DebugFlags.py and set disableSessionIdCheck to True"
            sys.exit()
        if responseObj["generateTestCase"]:
            print "Please edit DebugFlags.py and set generateTestCase to False"
            sys.exit()
        print "Please load the db using the appropriate data files before starting this test."
        
        scriptFile = open(fileName,"r")
        tests = scriptFile.read()
        script = "[" + tests + "]"
        scripts = json.loads(script)
        
        for script in scripts:
            httpMethod = script["httpRequestMethod"]
            if httpMethod == "POST":
                print "Testing " + script["testedFunction"]
                response = requests.post(script["requestUrl"])
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
            
    
            
        
    
    
    
    
    
    

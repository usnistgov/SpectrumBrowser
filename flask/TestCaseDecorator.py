'''
Created on Jun 3, 2015

@author: local
'''
import DebugFlags
import urlparse
from flask import request
import Config
import json
import os
import sys
import traceback
import util
# Note this is a nested function.
def testcase(original_function):
    def testcase_decorator(*args, **kwargs):
        try:
            if DebugFlags.getGenerateTestCaseFlag():
                p = urlparse.urlparse(request.url)
                urlpath = p.path
                pieces = urlpath.split("/")
                method = pieces[2]
                testFile = DebugFlags.getUnitTestFile()
                httpMethod = request.method
                response = original_function(*args, **kwargs)
                result = response.get_data()
                statusCode = response.status_code
                body = request.data
                testMap = {}
                testMap["statusCode"]=statusCode
                testMap["testedFunction"] = method
                testMap["httpRequestMethod"] = httpMethod
                if not Config.isSecure():
                    testMap["requestUrl"] = request.url
                else:
                    testMap["requestUrl"] = request.url.replace("http:","https:")
                if body != None:
                    testMap["requestBody"] = body
                testMap["expectedResponse"] = result
                toWrite = json.dumps(testMap,indent=4)
                if os.path.exists(testFile):
                    f = open(testFile,"a+")
                    f.write(",\n")
                else:
                    f = open(testFile,"w+")
                f.write(toWrite)
                f.write("\n")
                f.close()
                return response
            else:
                return  original_function(*args, **kwargs)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            util.logStackTrace(sys.exc_info())
            raise   
    return testcase_decorator
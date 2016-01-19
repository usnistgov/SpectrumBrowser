'''
Created on Feb 2, 2015

@author: local
'''
import os
import logging
import memcache

debug = True
disableAuthentication = False
# SET This to True for testing.
disableSessionIdCheck = False
# SET This to False for testing.
# Set this to True when generating test cases.
generateTestCase = False
# Note : In production we will set this to True
debugRelaxedPasswords = False
# File path to where the unit tests will be generated.
# Change this to where you want to generate unit tests.

unitTestFile = "unit-tests/unit-test.json"

if not "mc" in globals():
    mc = memcache.Client(['127.0.0.1:11211'], debug=0)

def setDefaults():
    global mc
    debugFlagDefaults = { "MSOD_DISABLE_AUTH":disableAuthentication, \
		      "MSOD_RELAXED_PASSWORDS":debugRelaxedPasswords,\
		      "MSOD_GENERATE_TEST_CASE":generateTestCase, \
		      "MSOD_DISABLE_SESSION_ID_CHECK":disableSessionIdCheck,\
		      "MSOD_DEBUG_LOGGING":debug}		
    mc.set("MSOD_DEBUG_FLAGS",debugFlagDefaults)

def getEnvBoolean(envVarName, override):
    global mc
    debugFlags = mc.get("MSOD_DEBUG_FLAGS")
    if debugFlags == None:
	return override
    if not envVarName in debugFlags:
	return override
    else:
    	return debugFlags[envVarName]

def getEnvString(envVarName, override):
    global mc
    flag = mc.get(envVarName)
    if flag == None:
        return override
    else:
        return flag

def getDebugFlag():
    return getEnvBoolean("MSOD_DEBUG_LOGGING", debug)

def getDebugFlags():
    global mc
    return mc.get("MSOD_DEBUG_FLAGS")

def setDebugFlags(debugFlags):
    global mc
    return mc.set("MSOD_DEBUG_FLAGS",debugFlags)


def getLogLevel():
    if getDebugFlag():
        return logging.DEBUG
    else:
        return logging.ERROR

def getDisableAuthenticationFlag():
    return getEnvBoolean("MSOD_DISABLE_AUTH", disableAuthentication)

def getDebugRelaxedPasswordsFlag():
    return getEnvBoolean("MSOD_RELAXED_PASSWORDS", debugRelaxedPasswords)

def getGenerateTestCaseFlag():
    return getEnvBoolean("MSOD_GENERATE_TEST_CASE", generateTestCase)

def getDisableSessionIdCheckFlag():
    return getEnvBoolean("MSOD_DISABLE_SESSION_ID_CHECK", disableSessionIdCheck)

def getUnitTestFile():
    return getEnvString("MSOD_UNIT_TEST_FILE", unitTestFile)


'''
Created on Feb 2, 2015

@author: local
'''
import os

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

# TODO -- get rid of environment variable read.
def getEnvBoolean(envVarName, override):
    flag = os.environ.get(envVarName)
    # print envVarName, flag
    if flag == None:
        return override
    else:
        return flag == "True"

def getEnvString(envVarName, override):
    flag = os.environ.get(envVarName)
    if flag == None:
        return override
    else:
        return flag

def getDebugFlag():
    return debug

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


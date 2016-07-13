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
Created on Feb 2, 2015

@author: local
'''
import os
import logging
import memcache
import Bootstrap
import util
from Defines import STATIC_GENERATED_FILE_LOCATION
sbHome = Bootstrap.getSpectrumBrowserHome()

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

if not "mc" in globals():
    mc = memcache.Client(['127.0.0.1:11211'], debug=0)


def setDefaults():
    global mc
    debugFlagDefaults = { "MSOD_DISABLE_AUTH":disableAuthentication, \
        "MSOD_RELAXED_PASSWORDS":debugRelaxedPasswords,\
        "MSOD_GENERATE_TEST_CASE":generateTestCase, \
        "MSOD_DISABLE_SESSION_ID_CHECK":disableSessionIdCheck,\
        "MSOD_DEBUG_LOGGING":debug}
    dirname = util.getPath(STATIC_GENERATED_FILE_LOCATION + "unit-tests")
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    mc.set("MSOD_DEBUG_FLAGS", debugFlagDefaults)


def getEnvBoolean(envVarName, override):
    global mc
    debugFlags = mc.get("MSOD_DEBUG_FLAGS")
    if debugFlags is None:
        return override
    if not envVarName in debugFlags:
        return override
    else:
        return debugFlags[envVarName]


def getEnvString(envVarName, override):
    global mc
    flag = mc.get(envVarName)
    if flag is None:
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
    return mc.set("MSOD_DEBUG_FLAGS", debugFlags)


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
    return getEnvBoolean("MSOD_DISABLE_SESSION_ID_CHECK",
                         disableSessionIdCheck)


def getUnitTestFile():
    dirname = util.getPath(STATIC_GENERATED_FILE_LOCATION + "unit-tests")
    return dirname + "/unit-test.json"

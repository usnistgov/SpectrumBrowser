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
Created on May 28, 2015

A script to load test data on to the database.

@author: mranga

'''
import json
import os
import sys

global msodConfig

msodConfig = None


def setupSensor(sensorConfigName):
    import SensorDb
    sensorConfig = json.load(open(sensorConfigName))
    SensorDb.addSensor(sensorConfig)

def parse_msod_config():
    if os.path.exists(os.environ.get("HOME") + "/.msod/MSODConfig.json"):
        configFile = open(os.environ.get("HOME") + "/.msod/MSODConfig.json")
    elif os.path.exists("/etc/msod/MSODConfig.json"):
        configFile = open("/etc/msod/MSODConfig.json")
    else:
        raise Exception("Config file not found.")
    msodConfig = json.load(configFile)
    return msodConfig

def setupConfig(configuration):
    import Config
    Config.setSystemConfig(configuration)

def setupSensors(pathPrefix = '.'):
    setupSensor(pathPrefix + "/E6R16W5XS.config.json")
    setupSensor(pathPrefix + "/ECR16W4XS.config.json")
    setupSensor(pathPrefix + "/Norfolk.config.json")

if __name__ == "__main__":
    config = parse_msod_config()
    sys.path.append(config["SPECTRUM_BROWSER_HOME"] + "/services/common")
    import Bootstrap
    Bootstrap.setPath()
    setupSensors()

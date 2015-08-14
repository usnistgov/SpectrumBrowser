'''
Created on May 28, 2015

@author: local
'''
import json
import os
import BootstrapPythonPath
BootstrapPythonPath.setPath()
import Config

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
        configFile = open(os.environ.get("HOME") + "/.msod/MSODConfig.json")
    else:
        raise Exception("Config file not found.")
    msodConfig = json.load(configFile)
    return msodConfig

def setupConfig(configuration):
    Config.setSystemConfig(configuration)

def setupSensors(pathPrefix = '.'):
    setupSensor(pathPrefix + "/E6R16W5XS.config.json")
    setupSensor(pathPrefix + "/E6R16W5XS1.config.json")
    setupSensor(pathPrefix + "/ECR16W4XS.config.json")
    setupSensor(pathPrefix + "/Norfolk.config.json")

if __name__ == "__main__":
    config = BootstrapPythonPath.parse_msod_config()
    setupConfig(config)
    setupSensors()



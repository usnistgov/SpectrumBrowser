'''
Created on May 28, 2015

@author: local
'''
import json
import os
import sys

global msodConfig

msodConfig = None


def setupSensor(sensorConfigName):

    sensorConfig = json.load(open(sensorConfigName))

    SensorDb.addSensor(sensorConfig)

def parse_msod_config():
    global msodConfig
    configFile = open(os.environ.get("HOME") + "/.msod/MSODConfig.json")
    msodConfig = json.load(configFile)

def setupConfig():
    import Config
    configuration = Config.parse_local_config_file("Config.unittest.txt")

    configuration["CERT"]=msodConfig["SPECTRUM_BROWSER_HOME"]+"/devel/certificates/dummy.crt"

    Config.setSystemConfig(configuration)


if __name__ == "__main__":
    global msodConfig
    parse_msod_config()
    sys.path.append(msodConfig["SPECTRUM_BROWSER_HOME"] + "/flask")
    setupConfig()
    import SensorDb
    import Config


    setupSensor("E6R16W5XS.config.json")
    setupSensor("ECR16W4XS.config.json")
    setupSensor("Norfolk.config.json")


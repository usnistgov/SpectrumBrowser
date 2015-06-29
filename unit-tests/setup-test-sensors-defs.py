'''
Created on May 28, 2015

@author: local
'''
import requests
import json
import os
import sys



def setupSensor(sensorConfigName):
    configFile = open(sensorConfigName)
    configStr = configFile.read()
    #confg = eval(configStr)
    sensorConfig = json.loads(configStr)
    SensorDb.addSensor(sensorConfig)

def setupConfig():
    configuration = Config.parse_local_config_file("Config.unittest.txt")
    configuration["CERT"]=os.getcwd()+"/dummy.crt"
    Config.setSystemConfig(configuration)


if __name__ == "__main__":

    if os.environ.get("SPECTRUM_BROWSER_HOME") == None:
        print "SpectrumBrowserHome is not set -- exitting"
        os._exit(0)
    sys.path.append(os.environ.get("SPECTRUM_BROWSER_HOME") + "/flask")
    import SensorDb
    import os
    import Config
    import populate_db

    setupConfig()

    setupSensor("E6R16W5XS.config.json")
    setupSensor("ECR16W4XS.config.json")
    setupSensor("Norfolk.config.json")


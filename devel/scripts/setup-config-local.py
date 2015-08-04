'''
Created on May 28, 2015

@author: local
'''
import sys
import argparse
import logging
import subprocess
import os
import json

logging.getLogger("spectrumbrowser").disabled = True

def getProjectHome():
    command = ['git', 'rev-parse', '--show-toplevel']
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return out.strip()

def setupConfig(host,configFile):
    msodConfig = json.load(open(os.environ.get("HOME")+ "/.msod/MSODConfig.json"))
    if "DB_DATA_DIR" in msodConfig:
        mongoDir = msodConfig["DB_DATA_DIR"]
    else:
        mongoDir = getProjectHome() + "/data/db"
    configuration = Config.parse_local_config_file(configFile)
    configuration["HOST_NAME"] = host
    configuration["CERT"] = getProjectHome() + "/devel/certificates/dummy.crt"
    configuration["MONGO_DIR"] = mongoDir
    Config.setSystemConfig(configuration)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument('-host',help='Host')
    parser.add_argument('-f',help='config file')
    args = parser.parse_args()
    configFile = args.f
    host = args.host
    sys.path.append(getProjectHome() + "/flask")
    import Config
    setupConfig(host,configFile)


import json as js
import sys
import subprocess
import os
def parse_msod_config():
    configFile = open(os.environ.get("HOME") + "/.msod/MSODConfig.json")
    msodConfig = js.load(configFile)
    return msodConfig

def getProjectHome(): #finds the default directory of installation
    command = ['git', 'rev-parse', '--show-toplevel']
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return out.strip()

def getSbHome():
    msodConfig = parse_msod_config()
    return str(msodConfig["SPECTRUM_BROWSER_HOME"])

def setPath():
    msodConfig = parse_msod_config()
    sbHome = str(msodConfig["SPECTRUM_BROWSER_HOME"])
    sys.path.append(sbHome + "/services/common")

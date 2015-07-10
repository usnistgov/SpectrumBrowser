'''
Created on May 28, 2015

@author: local
'''
import sys
import argparse


def setupConfig(host):
    configuration = Config.parse_local_config_file("Config.gburg.txt")
    configuration["CERT"]="/opt/SpectrumBrowser/flask/dummy.crt"
    configuration["HOST_NAME"] = host
    Config.setSystemConfig(configuration)


if __name__ == "__main__":
    sys.path.append("/opt/SpectrumBrowser/flask")
    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument('-host',help='Host')
    args = parser.parse_args()
    host = args.host
    import Config
    import logging
    logging.disable(logging.CRITICAL)
    setupConfig(host)


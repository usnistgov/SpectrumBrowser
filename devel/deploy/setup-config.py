'''
Created on May 28, 2015

@author: local
'''
import sys


def setupConfig():
    configuration = Config.parse_local_config_file("Config.gburg.txt")
    configuration["CERT"]="/opt/SpectrumBrowser/flask/dummy.crt"
    Config.setSystemConfig(configuration)


if __name__ == "__main__":
    sys.path.append("/opt/SpectrumBrowser/flask")
    import Config
    import logging
    logging.disable(logging.CRITICAL)
    setupConfig()


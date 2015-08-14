'''
utility program to clean debug logs.

Created on Jun 3, 2015

@author: local
'''

import Bootstrap
import os

def cleanLogs():
    flaskLogDir = Bootstrap.getFlaskLogDir()
    os.remove(flaskLogDir + "/" + "spectrumbrowser.log")
    
    
if __name__ == '__main__':
    cleanLogs()
    



import subprocess
import sys
import traceback
import os
import time



def readDiskUtil(diskDir):

    disk = 0
    if  diskDir != None :
            try :
                    df = subprocess.Popen(["df", diskDir], stdout=subprocess.PIPE)
                    sed = subprocess.Popen(["sed","1 d"] , stdin = df.stdout,stdout=subprocess.PIPE)
                    diskOutput = sed.communicate()[0]
                    disk = float(diskOutput.split()[4].split("%")[0])
            except :
                    print "Unexpected error:", sys.exc_info()[0]
                    print sys.exc_info()
                    traceback.print_exc()
                    os._exit(0)
    else :
            disk = 0

    return disk

if  __name__=='main':
    while True:
        diskUtil = readDiskUtil()
        time.sleep(30)

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


import subprocess
import sys
import traceback
import os
import time


def readDiskUtil(diskDir):

    disk = 0
    if diskDir is not None:
        try:
            df = subprocess.Popen(["df", diskDir], stdout=subprocess.PIPE)
            sed = subprocess.Popen(["sed", "1 d"],
                                   stdin=df.stdout,
                                   stdout=subprocess.PIPE)
            diskOutput = sed.communicate()[0]
            disk = float(diskOutput.split()[4].split("%")[0])
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()
            os._exit(0)
    else:
        disk = 0

    return disk

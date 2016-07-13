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
'''
Created on May 28, 2015

@author: local
'''
import os
import setup_test_sensors_defs as setupdefs
import sys

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-t")
    parser.add_argument("-p")
    args = parser.parse_args()
    testDataLocation = args.t
    prefix = args.p

    config = setupdefs.parse_msod_config()
    sys.path.append(config["SPECTRUM_BROWSER_HOME"] + "/services/common")
    import Bootstrap
    Bootstrap.setPath()

    setupdefs.setupSensors(prefix)

    if not os.path.exists(testDataLocation):
        print "Please put the test data at ", testDataLocation
        os._exit(0)

    import populate_db
    if not os.path.exists(testDataLocation +
                          "/LTE_UL_DL_bc17_bc13_ts109_p1.dat"):
        print("File not found " + testDataLocation +
              "/LTE_UL_DL_bc17_bc13_ts109_p1.dat")
    else:
        populate_db.put_data_from_file(testDataLocation +
                                       "/LTE_UL_DL_bc17_bc13_ts109_p1.dat")
    if not os.path.exists(testDataLocation +
                          "/LTE_UL_DL_bc17_bc13_ts109_p2.dat"):
        print("File not found " + testDataLocation +
              "/LTE_UL_DL_bc17_bc13_ts109_p2.dat")
    else:
        populate_db.put_data_from_file(testDataLocation +
                                       "/LTE_UL_DL_bc17_bc13_ts109_p2.dat")
    if not os.path.exists(testDataLocation +
                          "/LTE_UL_DL_bc17_bc13_ts109_p3.dat"):
        print("File not found " + testDataLocation +
              "/LTE_UL_DL_bc17_bc13_ts109_p3.dat")
    else:
        populate_db.put_data_from_file(testDataLocation +
                                       "/LTE_UL_DL_bc17_bc13_ts109_p3.dat")

    if not os.path.exists(testDataLocation + "/FS0714_173_7236.dat"):
        print("File not found " + testDataLocation + "/FS0714_173_7236.dat")
    else:
        populate_db.put_data_from_file(testDataLocation +
                                       "/FS0714_173_7236.dat")

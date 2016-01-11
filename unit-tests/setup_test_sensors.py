'''
Created on May 28, 2015

@author: local
'''
import os
import setup_test_sensors_defs as setupdefs
import BootstrapPythonPath
BootstrapPythonPath.setPath()
import sys
sys.path.append(BootstrapPythonPath.getSbHome() + "/services/spectrumbrowser")
import populate_db


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-t")
    parser.add_argument("-p")
    args = parser.parse_args()
    testDataLocation = args.t
    prefix = args.p

    setupdefs.setupSensors(prefix)

    if not os.path.exists(testDataLocation):
        print "Please put the test data at ", testDataLocation
        os._exit(0)

    if not os.path.exists(testDataLocation + "/v14FS0714_173_24243.dat"):
        print ("File not found " + testDataLocation + "/v14FS0714_173_24243.dat")
        os._exit(0)

    if not os.path.exists(testDataLocation + "/LTE_UL_DL_bc17_bc13_ts109_p1.dat"):
        print ("File not found " + testDataLocation + "/LTE_UL_DL_bc17_bc13_ts109_p1.dat")
        os._exit(0)

    if not os.path.exists(testDataLocation + "/LTE_UL_DL_bc17_bc13_ts109_p2.dat"):
        print ("File not found " + testDataLocation + "/LTE_UL_DL_bc17_bc13_ts109_p2.dat")
        os._exit(0)
    if not os.path.exists(testDataLocation + "/LTE_UL_DL_bc17_bc13_ts109_p3.dat"):
        print ("File not found " + testDataLocation + "/LTE_UL_DL_bc17_bc13_ts109_p3.dat")
        os._exit(0)
    populate_db.put_data_from_file(testDataLocation + "/LTE_UL_DL_bc17_bc13_ts109_p1.dat")
    populate_db.put_data_from_file(testDataLocation + "/LTE_UL_DL_bc17_bc13_ts109_p2.dat")
    populate_db.put_data_from_file(testDataLocation + "/LTE_UL_DL_bc17_bc13_ts109_p3.dat")
    populate_db.put_data_from_file(testDataLocation + "/v14FS0714_173_24243.dat")

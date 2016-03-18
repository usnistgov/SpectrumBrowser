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
    if not os.path.exists(testDataLocation + "/LTE_UL_DL_bc17_bc13_ts109_p1.dat"):
        print ("File not found " + testDataLocation + "/LTE_UL_DL_bc17_bc13_ts109_p1.dat")
    else:
        populate_db.put_data_from_file(testDataLocation + "/LTE_UL_DL_bc17_bc13_ts109_p1.dat")
    if not os.path.exists(testDataLocation + "/LTE_UL_DL_bc17_bc13_ts109_p2.dat"):
        print ("File not found " + testDataLocation + "/LTE_UL_DL_bc17_bc13_ts109_p2.dat")
    else:
        populate_db.put_data_from_file(testDataLocation + "/LTE_UL_DL_bc17_bc13_ts109_p2.dat")
    if not os.path.exists(testDataLocation + "/LTE_UL_DL_bc17_bc13_ts109_p3.dat"):
        print ("File not found " + testDataLocation + "/LTE_UL_DL_bc17_bc13_ts109_p3.dat")
    else:
        populate_db.put_data_from_file(testDataLocation + "/LTE_UL_DL_bc17_bc13_ts109_p3.dat")

    if not os.path.exists(testDataLocation + "/FS0714_173_7236.dat"):
        print ("File not found " + testDataLocation + "/FS0714_173_7236.dat")
    else:
       populate_db.put_data_from_file(testDataLocation + "/FS0714_173_7236.dat")

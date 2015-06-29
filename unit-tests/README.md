<h2>This directory contains unit test scripts </h2>

After starting msdod and mongodb, you can set up for testing as follows:

Populate the DB with test data (I am using the LTE data as an example for test purposes)
    
    define an environment variable TEST_DATA_HOME
    mkdir $TEST_DATA_HOME
   
Put the following files in $TEST_DATA_HOME

     FS0714_173_7236.dat  
     LTE_UL_DL_bc17_bc13_ts109_p1.dat  
     LTE_UL_DL_bc17_bc13_ts109_p2.dat  
     LTE_UL_DL_bc17_bc13_ts109_p3.dat
     LTE_UL_bc17_ts109_stream_30m.dat

    This will run for a while ( about 5 minutes)

    (these files are not on github - too big. Ask mranga@nist.gov for data files when you are ready for this step.)

The following is a description of the test scripts in this directory:


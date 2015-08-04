<H2>Startup Scripts for development and testing</H2>

The scripts here are for development and test purposes. It may be easier to use these scripts than to start/stop services:

  start-db.sh : Starts mongod (the data is placed in $HOME/.msod/MSODConfig.json[SPECTRUM_BROWSER_HOME][DB_DATA_DIR] )
  start-msod.sh : Starts msod (all except for the database - you have to start the database first.)
  start-msod-generate-testcases.sh : Starts msod for generating unit tests.
  start-msod-run-testcases.sh : Starts msod for running test cases.
  stop-msod.sh : Stops msod
  stop-db.sh: stops mongod (assumes it is colocated).

You can configure a running instance of msod using 
  
  python setup-config-local.py -f Config.gburg.txt -host msod.ip.address

Where msod.ip.address is the IP address assigned to the msod instance.


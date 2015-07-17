<H2>Startup Scripts (for development)</H2>

The scripts here are for development and test purposes. It may be easier to use these scripts than to start/stop services:

  start-db.sh : Starts mongod (the data is placed in $HOME/.msod/MSODConfig.json )
  start-msod.sh : Starts msod (all except for the database)
  start-msod-generate-testcases.sh : Starts msod for generating unit tests.
  start-msod-run-testcases.sh : Starts msod for running test cases.
  stop-msod.sh : Stops msod
  stop-db.sh: stops mongod (assumes it is colocated).

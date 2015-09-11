#!/bin/bash
ps cax | grep memcached > /dev/null
if [ $? -eq 0 ]; then
  echo "memcached is running. run stop-msod.sh"
  exit 0
fi
memcached&
pid=$!
echo $pid > .memcached.pid
disown $pid
ps cax | grep gunicorn > /dev/null
if [ $? -eq 0 ]; then
  echo "Process is running. run stop-msod.sh"
  exit 1
fi
CFG=$HOME/.msod/MSODConfig.json
if [ -f $FILE  ]; then
    echo "Using file $CFG"
else
    print "$CFG not found"
    exit -1
fi
SB_HOME=$(
    python -c 'import json; print json.load(open("'$CFG'"))["SPECTRUM_BROWSER_HOME"]'
)
if [ -z "$SB_HOME"  ]; then
    echo "$SB_HOME is empty"
    exit -1
fi
DB_DATA_DIR=$(
    python -c 'import json; print json.load(open("'$CFG'"))["DB_DATA_DIR"]'
)

export PYTHONPATH=$SB_HOME/services/common:$SB_HOME/services/spectrumbrowser:$PYTHONPATH
python $SB_HOME/common/CleanLogs.py
rm -f .gunicorn.pid
gunicorn -w 4 -k flask_sockets.worker flaskr:app  --pythonpath=${PYTHONPATH} -b '0.0.0.0:8000' --debug --log-file - --error-logfile -&
pid=$!
echo $pid > .gunicorn.pid
disown $pid
python $SB_HOME/services/servicecontrol/ServiceControlFunctions.py --daemon False&
pid=$!
echo $pid > .servicecontrol.pid
disown $pid
python $SB_HOME/services/admin/Admin.py --daemon False&
pid=$!
echo $pid > .admin.pid
disown $pid
#Start resource data streaming service
python $SB_HOME/services/webmonitor/ResourceStreamingServer.py --daemon False&
pid=$!
disown $pid
#Start resource data streaming service
python $SB_HOME/services/dbmonitor/ResourceMonitor.py --daemon False --dbpath=$DB_DATA_DIR&
pid=$!
disown $pid
#Start db monitoring service
python $SB_HOME/services/streaming/StreamingServer.py --daemon False&
pid=$!
disown $pid
#Start occupancy alert service
python $SB_HOME/services/occupancy/OccupancyAlert.py --daemon False&
pid=$!
disown $pid
#Start federation service
python $SB_HOME/services/federation/FederationService.py --daemon False&
pid=$!
disown $pid

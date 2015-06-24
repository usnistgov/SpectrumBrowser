#!/bin/bash
ps cax | grep memcached > /dev/null
if [ $? -eq 0 ]; then
  echo "memcached is running. run stop-gunicorn.sh"
  exit 0
fi
memcached&
pid=$!
echo $pid > .memcached.pid
disown $pid
ps cax | grep gunicorn > /dev/null
if [ $? -eq 0 ]; then
  echo "Process is running. run stop-gunicorn.sh"
  exit 1
fi
CFG=$HOME/.msod/MSODConfig.json
SB_HOME=$(
    python -c 'import json; print json.load(open("'$CFG'"))["SPECTRUM_BROWSER_HOME"]'
)
export PYTHONPATH=$SB_HOME/flask:$PYTHONPATH
python $SB_HOME/flask/CleanLogs.py
rm -f .gunicorn.pid
gunicorn -w 4 -k flask_sockets.worker flaskr:app  -b '0.0.0.0:8000' --debug --log-file - --error-logfile -&
pid=$!
echo $pid > .gunicorn.pid
disown $pid
python $SB_HOME/flask/Admin.py&
pid=$!
echo $pid > .admin.pid
disown $pid
python $SB_HOME/flask/StreamingServer.py&
pid=$!
echo $pid > .streaming.pid
disown $pid
#Start occupancy alert service
python $SB_HOME/flask/OccupancyAlert.py&
pid=$!
echo $pid > .occupancy.pid
disown $pid
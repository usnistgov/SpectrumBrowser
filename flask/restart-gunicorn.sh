kill -INT $(cat .gunicorn.pid)
kill -9 $(cat .admin.pid)
kill -INT $(cat .memcached.pid)
kill -INT $(cat .streaming.pid)
kill -9 $(cat .occupancy.pid)
rm .gunicorn.pid .admin.pid .memcached.pid .streaming.pid .occupancy.pid
sleep 5
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
rm -f .gunicorn.pid
python CleanLogs.py

#gunicorn -w 4 -k flask_sockets.worker flaskr:app  -b '0.0.0.0:8000' --debug --log-file - --error-logfile -
gunicorn -w 4 -k flask_sockets.worker flaskr:app  -b '0.0.0.0:8000' --debug --log-file - --error-logfile -&
pid=$!
disown $pid
echo $pid > .gunicorn.pid
#Start Admin service
python Admin.py&
pid=$!
disown $pid
echo $pid > .admin.pid
python StreamingServer.py&
pid=$!
disown $pid
echo $pid > .datastreaming.pid
#Start occupancy alert service
python OccupancyAlert.py&
pid=$!
disown $pid
echo $pid > .occupancy_alert.pid





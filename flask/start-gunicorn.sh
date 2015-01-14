ps cax | grep gunicorn > /dev/null
if [ $? -eq 0 ]; then
  echo "Process is running."
  exit 1
fi
rm -f .gunicorn.pid
#gunicorn -w 4 -k flask_sockets.worker flaskr:app  -b '0.0.0.0:8000' --debug --log-file - --error-logfile -
gunicorn -w 4 -k flask_sockets.worker flaskr:app  -b '0.0.0.0:8000' --debug --log-file - --error-logfile -&
pid=$!
disown $pid
echo $pid > .gunicorn.pid
ps cax | grep memcached > /dev/null
if [ $? -eq 0 ]; then
  echo "memcached is running."
  exit 0
fi
memcached&
pid=$!
disown $pid




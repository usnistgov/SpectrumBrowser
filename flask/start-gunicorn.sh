rm -f .gunicorn.pid
gunicorn -w 4 -k flask_sockets.worker flaskr:app  -b '0.0.0.0:8000' --debug --log-file - --error-logfile -
pid=$!
echo $pid > .gunicorn.pid

#gunicorn -w 1 -k flask_sockets.worker flaskr:app  -b '0.0.0.0:8000' --debug --log-file - --error-logfile -


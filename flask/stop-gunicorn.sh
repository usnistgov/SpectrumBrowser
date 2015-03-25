kill -9 $(cat .gunicorn.pid)
kill -9 $(cat .memcached.pid)
kill -9 `ps | grep gunicorn | sed s/' '+/' '/g|cut -d ' ' -f 2`

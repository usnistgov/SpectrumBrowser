#!/bin/bash
kill -INT $(cat .gunicorn.pid)
kill -INT $(cat .servicecontrol.pid)
kill -TERM $(cat .servicecontrol.pid)
kill -INT $(cat .admin.pid)
kill -TERM $(cat .admin.pid)
kill -INT $(cat .memcached.pid)
kill -TERM $(cat .memcached.pid)
kill -INT $(cat .streaming.pid)
kill -TERM $(cat .streaming.pid)
kill -INT $(cat .occupancy.pid)
kill -TERM $(cat .occupancy.pid)
kill -INT $(cat .monitoring.pid)
kill -TERM $(cat .monitoring.pid)
kill -INT $(cat .federation.pid)
kill -TERM $(cat .federation.pid)
kill -9 `ps | grep gunicorn | sed s/' '+/' '/g|cut -d ' ' -f 2`
rm -f .servicecontrol.pid .gunicorn.pid .admin.pid .memcached.pid .streaming.pid .monitoring.pid .federation.pid

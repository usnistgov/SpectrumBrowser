#!/bin/bash
kill -INT $(cat .gunicorn.pid)
kill -9 $(cat .admin.pid)
kill -INT $(cat .memcached.pid)
kill -INT $(cat .streaming.pid)
kill -INT $(cat .occupancy.pid)
kill -INT $(cat .monitoring.pid)
kill -9 `ps | grep gunicorn | sed s/' '+/' '/g|cut -d ' ' -f 2`
rm -f .gunicorn.pid .admin.pid .memcached.pid .streaming.pid .monitoring.pid

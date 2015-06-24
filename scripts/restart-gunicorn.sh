#!/bin/bash
kill -INT $(cat .gunicorn.pid)
kill -9 $(cat .admin.pid)
kill -INT $(cat .memcached.pid)
kill -INT $(cat .streaming.pid)
kill -INT $(cat .occupancy.pid)
rm .gunicorn.pid .admin.pid .memcached.pid .streaming.pid .occupancy.pid
sleep 5
source start-gunicorn.sh





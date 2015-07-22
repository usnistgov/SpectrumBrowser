#!/bin/bash
kill -INT $(cat .gunicorn.pid)
kill -9 $(cat .admin.pid)
kill -INT $(cat .memcached.pid)
kill -INT $(cat .streaming.pid)
kill -INT $(cat .occupancy.pid)
kill -INT $(cat .resourceStreaming.pid)
kill -9 `ps | grep gunicorn | sed s/' '+/' '/g|cut -d ' ' -f 2`
rm .gunicorn.pid .admin.pid .memcached.pid .streaming.pid .resourceStreaming.pid

#!/bin/sh
# `/sbin/setuser spectrum` runs the given command as the user `spectrum`.
#exec /sbin/setuser spectrum /usr/bin/spectrum_monitor_post >>/var/log/spectrum_monitor.log 2>&1
exec /sbin/setuser spectrum /usr/bin/spectrum_monitor_post

#! /usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
#This software was developed by employees of the National Institute of
#Standards and Technology (NIST), and others.
#This software has been contributed to the public domain.
#Pursuant to title 15 Untied States Code Section 105, works of NIST
#employees are not subject to copyright protection in the United States
#and are considered to be in the public domain.
#As a result, a formal license is not needed to use this software.
#
#This software is provided "AS IS."
#NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
#OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
#MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
#AND DATA ACCURACY.  NIST does not warrant or make any representations
#regarding the use of the software or the results thereof, including but
#not limited to the correctness, accuracy, reliability or usefulness of
#this software.

import pytz
import datetime
import calendar
import time
import json
import argparse
import sys
import httplib
from dateutil import tz
from datetime import timedelta
import Config

SECONDS_PER_DAY = 24 * 60 * 60


def parseTime(timeString, timeZone):
    ts = time.mktime(time.strptime(timeString, '%Y-%m-%d %H:%M:%S'))
    (localTime, tzName) = getLocalTime(ts, timeZone)
    return localTime


def getLocalTime(utcTime, timeZone):
    """
    get the local time from a utc timestamp given the timezone
    """
    to_zone = tz.gettz(timeZone)
    utc = datetime.datetime.utcfromtimestamp(utcTime)
    from_zone = tz.gettz('UTC')
    utc = utc.replace(tzinfo=from_zone)
    todatetime = utc.astimezone(to_zone)
    localTime = calendar.timegm(todatetime.timetuple())
    return (localTime, todatetime.tzname())


def is_dst(localTime, zonename):
    tz = pytz.timezone(zonename)
    now = pytz.utc.localize(datetime.datetime.fromtimestamp(localTime))
    return now.astimezone(tz).dst() != timedelta(0)


def getDateTimeFromLocalTimeStamp(ts):
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    return st


def getDayBoundaryTimeStampFromUtcTimeStamp(timeStamp, timeZoneId):
    """
    get to the day boundary given a local time in the UTC timeZone.
    ts is the local timestamp in the UTC timeZone i.e. what you would
    get from time.time() on your computer + the offset betwen your
    timezone and UTC.
    """
    (ts, tzName) = getLocalTime(timeStamp, timeZoneId)
    timeDiff = timeStamp - ts
    dt = datetime.datetime.fromtimestamp(float(ts))
    dt1 = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    isDst = is_dst(ts, timeZoneId)
    dbts = int(dt1.strftime("%s"))
    return dbts + timeDiff


def formatTimeStamp(timeStamp):
    """
    only year month and day timestamp.
    """
    dt = datetime.datetime.fromtimestamp(float(timeStamp))
    return dt.strftime('%Y-%m-%d')


def formatTimeStampLong(timeStamp, timeZoneName):
    """
    long format timestamp.
    """
    localTimeStamp, tzName = getLocalTime(timeStamp, timeZoneName)
    dt = datetime.datetime.fromtimestamp(float(localTimeStamp))
    return str(dt) + " " + tzName


def getLocalTimeZoneFromGoogle(time, lat, long):
    try:
        conn = httplib.HTTPSConnection("maps.googleapis.com")
        conn.request("POST", "/maps/api/timezone/json?location=" +
                     str(lat) + "," + str(long) + "&timestamp=" +
                     str(time) + "&sensor=false&key=" + Config.getApiKey(), "",
                     {"Content-Length":0})
        res = conn.getresponse()
        if res.status == 200:
            data = res.read()
            print data
            jsonData = json.loads(data)
            return (jsonData["timeZoneId"], jsonData["timeZoneName"])
        else:
            print "Status ", res.status, res.reason
            return (None, None)
    except:
        print sys.exc_info()[0]
        return (None, None)


def getTimeOffsetFromGoogle(time,lat, long):
    try:
        API_KEY = Config.getApiKey()
        conn = httplib.HTTPSConnection("maps.googleapis.com")
        conn.request("POST", "/maps/api/timezone/json?location=" +
                     str(lat) + "," + str(long) + "&timestamp=" +
                     str(time) + "&sensor=false&key=" + API_KEY, "",
                     {"Content-Length":0})
        res = conn.getresponse()
        if res.status == 200: 
            data = res.read()
            print data
            jsonData = json.loads(data)
            if "errorMessage" not in jsonData:
                offset = jsonData["rawOffset"] + jsonData["dstOffset"]
                return offset
            else:
                raise Exception("Error communicating with google")
        else:
            raise Exception("Error communicating with google")
    except:
        raise


def getLocalUtcTimeStamp():
    t = time.mktime(time.gmtime())
    isDst = time.localtime().tm_isdst
    return t - isDst * 60 * 60


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument('-t', help='current global time')
    parser.add_argument('-tz', help='time zone')
    args = parser.parse_args()
    print getTimeOffsetFromGoogle(time.time(),39, -77)

    if args.t is not None:
        t = int(args.t)
    else:
        t = getLocalUtcTimeStamp()

    if args.tz is not None:
        tzId = args.tz
    else:
        tzId = "America/New_York"
    print "-----------------------------------"
    print tzId
    print formatTimeStampLong(t, tzId)
    startOfToday = getDayBoundaryTimeStampFromUtcTimeStamp(t, tzId)
    print "Day Boundary Long Formatted TimeStamp for start of the day", formatTimeStampLong(
        startOfToday, tzId)
    (localtime, tzname) = getLocalTime(startOfToday, tzId)
    delta = startOfToday - localtime
    print "dayBoundaryTimeStamp = ", startOfToday, \
          "getLocalTime(startOfToday,tzId) = ", localtime, " Delta  =  ", delta / 60 / 60, " Hours"
    print "getDayBoundaryTimeStampFromUtcTimeStamp returned ", startOfToday
    print "Computed time ahead of midnight " + str(float(t - startOfToday) /
                                                   float(3600)), " Hours"
    print "Current offset from gmt ", int((parseTime(
        getDateTimeFromLocalTimeStamp(time.time()), "America/New_York") -
                                      time.time()) / (60 * 60))

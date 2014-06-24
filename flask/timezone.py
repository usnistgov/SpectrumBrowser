import pytz
import datetime
import calendar
import time
import json
import argparse
import sys
import httplib
import dateutil
from dateutil import tz
import datetime
from datetime import timedelta

SECONDS_PER_DAY = 24*60*60


def getLocalTime(utcTime,timeZone):
    """
    get the local time from a utc timestamp given the timezone
    """
    to_zone = tz.gettz(timeZone)
    utc = datetime.datetime.utcfromtimestamp(utcTime)
    from_zone = tz.gettz('UTC')
    utc = utc.replace(tzinfo=from_zone)
    todatetime = utc.astimezone(to_zone)
    localTime = calendar.timegm(todatetime.timetuple())
    return (localTime,todatetime.tzname())

def is_dst(localTime, zonename):
    tz = pytz.timezone(zonename)
    now = pytz.utc.localize(datetime.datetime.fromtimestamp(localTime))
    return now.astimezone(tz).dst() != timedelta(0)





def getDayBoundaryTimeStampFromUtcTimeStamp(timeStamp,timeZoneId):
    """
    get to the day boundary given a local time in the UTC timeZone.
    ts is the local timestamp in the UTC timeZone i.e. what you would
    get from time.time() on your computer + the offset betwen your 
    timezone and UTC.
    """
    (ts,tzName) = getLocalTime(timeStamp,timeZoneId)
    timeDiff = timeStamp - ts
    dt = datetime.datetime.fromtimestamp(float(ts))
    dt1 = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    isDst = is_dst(ts,timeZoneId)
    dbts = int(dt1.strftime("%s"))
    return dbts + timeDiff 



def formatTimeStamp(timeStamp):
    """
    only year month and day timestamp.
    """
    dt = datetime.datetime.fromtimestamp(float(timeStamp))
    return dt.strftime('%Y-%m-%d')

def formatTimeStampLong(timeStamp,timeZoneName):
    """
    long format timestamp.
    """
    localTimeStamp,tzName = getLocalTime(timeStamp,timeZoneName)
    dt = datetime.datetime.fromtimestamp(float(localTimeStamp))
    return str(dt) + " " + tzName


API_KEY= "AIzaSyDgnBNVM2l0MS0fWMXh3SCzBz6FJyiSodU"
def getLocalTimeZoneFromGoogle(time, lat, long):
    try :
        conn = httplib.HTTPSConnection("maps.googleapis.com")
        conn.request("POST","/maps/api/timezone/json?location="+str(lat)+","+str(long)+"&timestamp="+str(time)+"&sensor=false&key=" + API_KEY,"",\
                {"Content-Length":0})
        res = conn.getresponse()
        if res.status == 200 :
            data = res.read()
            print data
            jsonData = json.loads(data)
            return (jsonData["timeZoneId"],jsonData["timeZoneName"])
        else :
            print "Status ", res.status, res.reason
            return (None,None)
    except :
        print sys.exc_info()[0]
        return (None,None)

def getLocalUtcTimeStamp():
     t =  time.mktime(time.gmtime())
     isDst = time.localtime().tm_isdst
     return t - isDst*60*60


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument('-t',help='current global time')
    parser.add_argument('-tz',help='time zone')
    args = parser.parse_args()

    if args.t != None:
        t = int(args.t)
    else:
        t =  getLocalUtcTimeStamp()

    if args.tz != None:
        tzId = args.tz
    else:
        tzId = "America/New_York"
    print "-----------------------------------"
    print tzId
    print formatTimeStampLong(t ,tzId)
    startOfToday = getDayBoundaryTimeStampFromUtcTimeStamp(t ,tzId)
    print "Day Boundary Long Formatted TimeStamp for start of the day", formatTimeStampLong(startOfToday,tzId)
    (localtime,tzname) =  getLocalTime(startOfToday,tzId)
    delta = startOfToday - localtime
    print "dayBoundaryTimeStamp = " , startOfToday, \
          "getLocalTime(startOfToday,tzId) = " , localtime, " Delta  =  " , delta/60/60, " Hours"
    print "getDayBoundaryTimeStampFromUtcTimeStamp returned " , startOfToday
    print "Computed time ahead of midnight " +  str(float(t  - startOfToday)/float(3600)), " Hours"





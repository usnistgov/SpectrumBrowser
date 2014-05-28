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

def getTimeStamp(timeStamp,timeZoneId):
    """ 
    get the UTC timestamp corresponding to a local timestamp
    given the timeZoneId.
    timestamp is the STANDARD time in the timeZoneId.
    for example, the timeStamp should be in EST not EDT. 
    """
    retval=  int(time.mktime(datetime.datetime.fromtimestamp(float(timeStamp),tz=pytz.timezone(timeZoneId)).utctimetuple()))
    return retval

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


def getDayBoundaryTimeStamp(ts,timeZoneId):
    """
    get to the day boundary given a local time.
    ts is the local timestamp. i.e. what you would
    get from time.time() on your computer.
    """
    timeStamp = getTimeStamp(ts,timeZoneId)
    dt = datetime.datetime.fromtimestamp(float(timeStamp))
    dt1 = datetime.datetime(*dt.timetuple()[:3])
    return int(dt1.strftime("%s"))


def getDayBoundaryTimeStampFromUtcTimeStamp(timeStamp):
    """
    get to the day boundary given a local time in the UTC timeZone.
    ts is the local timestamp in the UTC timeZone i.e. what you would
    get from time.time() on your computer + the offset betwen your 
    timezone and UTC.
    """
    dt = datetime.datetime.fromtimestamp(float(timeStamp))
    dt1 = datetime.datetime(*dt.timetuple()[:3])
    return int(dt1.strftime("%s"))



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
    dt = datetime.datetime.fromtimestamp(float(timeStamp))
    return str(dt) + " " + timeZoneName


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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process command line args')
    parser.add_argument('-t',help='current global time')
    parser.add_argument('-tz',help='time zone')
    args = parser.parse_args()
    if args.t != None:
        t = int(args.t)
    else:
        t =  time.mktime(time.localtime())
        isDst = time.localtime().tm_isdst
        standard_time = t - isDst*60*60

    if args.tz != None:
        tzId = args.tz
    else:
        tzId = "America/New_York"
    t1 = getTimeStamp(standard_time ,tzId)
    print "Local Time " , t , "getTimeStamp Returned", t1 
    diff =  t1 - t
    print "diff ", diff
    #print "-----------------------"
    #print "Boston", str(getLocalTimeZoneFromGoogle(standard_time,44,-71.1))
    #print "Chcago", str(getLocalTimeZoneFromGoogle(standard_time,41.9, -87.6))
    #print "Denver", str(getLocalTimeZoneFromGoogle(standard_time,39.7, -105.0))
    #print "Phoenix", str(getLocalTimeZoneFromGoogle(standard_time,33.5, -112.1))
    #print "LA", str(getLocalTimeZoneFromGoogle(standard_time,34.1, -118.3))
    startOfToday = getDayBoundaryTimeStamp(standard_time,tzId)
    print formatTimeStamp(startOfToday)
    print formatTimeStampLong(startOfToday,tzId)
    (localtime,tzname) =  getLocalTime(startOfToday,tzId)
    print "UtcTimeStartOfToday = " , startOfToday
    print "LocalTimeStartOfToday = " , localtime
    delta = startOfToday - localtime
    print "Delta  =  " , delta
    timeStampStartOfToday = getTimeStamp(startOfToday,tzId)
    utcTimeStartOfToday = getDayBoundaryTimeStampFromUtcTimeStamp(timeStampStartOfToday)
    print "UTC Time start of today ",utcTimeStartOfToday
    currentTime = time.time()
    print "Time ahead of midnight today right now " +  str(float(currentTime - utcTimeStartOfToday)/float(3600))





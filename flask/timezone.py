import pytz
import datetime
import calendar
import time
import json
import argparse
import sys
import httplib

def getTimeStamp(timeStamp,timeZoneId):
    retval=  int(time.mktime(datetime.datetime.fromtimestamp(float(timeStamp),tz=pytz.timezone(timeZoneId)).utctimetuple()))
    return retval

# get to the day boundary and add the timezone offset.
def getDayBoundaryTimeStamp(ts,timeZoneId):
    timeStamp = getTimeStamp(ts,timeZoneId)
    dt = datetime.datetime.fromtimestamp(float(timeStamp))
    dt1 = datetime.datetime(*dt.timetuple()[:3])
    return int(dt1.strftime("%s"))

def formatTimeStamp(timeStamp):
    dt = datetime.datetime.fromtimestamp(float(timeStamp))
    return dt.strftime('%Y-%m-%d')

def formatTimeStampLong(timeStamp,timeZoneName):
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
        tz = args.tz
    else:
        tz = "America/New_York"
    t1 = getTimeStamp(standard_time ,tz)
    print "Local Time " , t , "getTimeStamp Returned", t1 
    diff =  t1 - t
    print "diff ", diff
    #print "-----------------------"
    #print "Boston", str(getLocalTimeZoneFromGoogle(standard_time,44,-71.1))
    #print "Chcago", str(getLocalTimeZoneFromGoogle(standard_time,41.9, -87.6))
    #print "Denver", str(getLocalTimeZoneFromGoogle(standard_time,39.7, -105.0))
    #print "Phoenix", str(getLocalTimeZoneFromGoogle(standard_time,33.5, -112.1))
    #print "LA", str(getLocalTimeZoneFromGoogle(standard_time,34.1, -118.3))
    today = getDayBoundaryTimeStamp(t,tz)
    print formatTimeStamp(today)



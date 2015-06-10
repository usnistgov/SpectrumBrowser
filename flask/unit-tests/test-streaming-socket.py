import argparse
import socket
import requests
import sys
import time
import ssl
import json as js
import os

secure = True

if __name__ == "__main__":
    print os.environ.get("SPECTRUM_BROWSER_HOME")
    sys.path.append(os.environ.get("SPECTRUM_BROWSER_HOME") + "/flask")
    import timezone
    parser = argparse.ArgumentParser(description="Process command line args")
    parser.add_argument("-data",help="File name to stream")
    parser.add_argument("-sensorId",help="sensorId")
    args = parser.parse_args()
    filename = args.data
    if filename == None:
        print "please specify -data filename"
        sys.exit()
    sensorId = args.sensorId
    if sensorId == None:
        print "Please specify sensorID"
        sys.exit()
    r = requests.post("http://localhost:8000/sensordata/getStreamingPort/"+sensorId)
    json = r.json()
    port = json["port"]
    print "port = ", port
    r = requests.post("http://localhost:8000/sensordb/getSensorConfig/"+sensorId)
    json = r.json()
    print json
    if json["status"] != "OK":
        print json["ErrorMessage"]
        os._exit()
    if not json["sensorConfig"]["isStreamingEnabled"]:
        print "Streaming is not enabled"
        print json
        os._exit(1)
    timeBetweenReadings = float(json["sensorConfig"]["streaming"]["streamingSecondsPerFrame"])
    if not secure:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("localhost",port))
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock = ssl.wrap_socket(s, ca_certs="dummy.crt",cert_reqs=ssl.CERT_OPTIONAL)
        sock.connect(('localhost', port))
    headersSent = False
    with open(filename,"r") as f:
        while True:
            # Read and send system,loc and data message.
            if not headersSent :
                for i in range(0,3):
                    readBuffer = ""
                    while True:
                        byte = f.read(1)
                        if byte == "\r":
                            break;
                        readBuffer = readBuffer + byte
                    bytesToRead = int(readBuffer)
                    toSend = f.read(bytesToRead)

                    headerToSend = js.loads(str(toSend))
                    headerToSend["SensorID"] = sensorId
                    headerToSend["t"],tzName = timezone.getLocalTime(time.time(),"America/New_York")
                    if headerToSend["Type"] == "Data" :
                        headerToSend["mPar"]["tm"] = timeBetweenReadings

                    toSend = js.dumps(headerToSend,indent=4)
                    length = len(toSend)
                    print toSend
                    sock.send(str(length) + "\n")
                    sock.send(toSend)
                    print "Header sent"
                headersSent = True
            time.sleep(timeBetweenReadings)
            toSend = f.read(56)
            sock.send(toSend)


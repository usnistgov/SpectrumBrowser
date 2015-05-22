import argparse
import socket
import requests
import sys
import time
import ssl
import json as js

secure = True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process command line args")
    parser.add_argument("-data",help="File name to stream")
    args = parser.parse_args()
    filename = args.data
    if filename == None:
        print "please specify -data filename"
        sys.exit()
    r = requests.post("http://localhost:8000/sensordata/getStreamingPort/ECR16W4XS")
    json = r.json()
    port = json["port"]
    print "port = ", port
    r = requests.post("http://localhost:8000/sensordb/getSensorConfig/ECR16W4XS")
    json = r.json()
    print json
    if json["status"] != "OK":
        print json["ErrorMessage"]
        os._exit()
    if not json["sensorConfig"]["isStreamingEnabled"]:
        print "Streaming is not enabled"
        os._exit()
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
           

import argparse
import socket
import requests
import sys

secure = False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process command line args")
    parser.add_argument("-data",help="File name to stream")
    args = parser.parse_args()
    filename = args.data
    if filename == None:
        print "please specify -data filename"
        sys.exit()
    r = requests.post("http://localhost:8000/sensordata/getStreamingPort")
    json = r.json()
    port = json["port"]
    print "port = ", port
    if not secure:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("localhost",port))
    with open(filename,"r") as f:
        while True:
            toSend = f.read(64)
            sock.send(toSend)

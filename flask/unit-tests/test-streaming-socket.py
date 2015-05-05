import argparse
import socket
import requests
import sys
import time
import ssl

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
    if not secure:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("localhost",port))
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock = ssl.wrap_socket(s, ca_certs="dummy.crt",cert_reqs=ssl.CERT_OPTIONAL)
        sock.connect(('localhost', port))

    with open(filename,"r") as f:
        while True:
            toSend = f.read(56)
            sock.send(toSend)
            time.sleep(.0009)

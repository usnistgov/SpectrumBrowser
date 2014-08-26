from websocket import create_connection
import argparse
import binascii
import ssl

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process command line args")
    parser.add_argument("-data",help="File name to stream")
    args = parser.parse_args()
    filename = args.data
    ws = create_connection("wss://localhost:8443/spectrumdb/stream",sslopt=dict(cert_reqs=ssl.CERT_NONE))
    with open(filename,"r") as f:
        while True:
            bytes = f.read(64)
            toSend = binascii.b2a_base64(bytes)
            ws.send(toSend)

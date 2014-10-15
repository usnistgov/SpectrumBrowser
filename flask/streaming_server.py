import socket
import ssl
import argparse


bindsocket = socket.socket()
bindsocket.bind(('', 10023))
bindsocket.listen(5)

def do_something(connstream, data):
    print "do_something:", data
    return False

def deal_with_client(connstream):
    data = connstream.read()
    while data:
        data = connstream.read()

while True:
    newsocket, fromaddr = bindsocket.accept()
    connstream = ssl.wrap_socket(newsocket,
                                 server_side=True,
                                 certfile="dummy.crt",
                                 )
    try:
        t = threading.Thread(target=deal_with_client, args = connstream)
        deal_with_client(connstream)
    finally:
        connstream.shutdown(socket.SHUT_RDWR)
        connstream.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process command line args')

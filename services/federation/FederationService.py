import Bootstrap
Bootstrap.setPath()
import PeerConnectionManager
import util
import argparse
import signal
import Log
import os

def signal_handler(signo, frame):
    print('Connection Maintainer : Caught signal! Exiting.')
    os._exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)
    parser = argparse.ArgumentParser()
    parser.add_argument("--pidfile", default=".federation.pid")
    args = parser.parse_args()

    print "Starting federation service"
    with util.PidFile(args.pidfile):
        Log.configureLogging("federation")
        connectionMaintainer = PeerConnectionManager.ConnectionMaintainer()
        connectionMaintainer.start()

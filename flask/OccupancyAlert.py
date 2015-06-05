'''
Created on Jun 4, 2015

@author: local
'''
import threading
import ssl
import traceback
import util
import Config
import sys
import zmq
import json
import socket
from bitarray import bitarray

from DataStreamSharedState import MemCache

isSecure = True

class OccupancyWorker(threading.Thread):   
    def __init__(self,conn):
        threading.Thread.__init__(self)
        self.conn = conn
        context = zmq.Context()
        self.sock= context.socket(zmq.SUB)
        self.memcache = MemCache()        
        
   
        
    def run(self):
        sensorId = None
        try:
            c = ""
            jsonStr = ""
            while c != "}":
                c= self.conn.recv(1)
                jsonStr  = jsonStr + c
            jsonObj = json.loads(jsonStr)
            print "subscription received for " + jsonObj["SensorID"]
            sensorId = jsonObj["SensorID"]
            self.sensorId = sensorId
            self.sock.setsockopt_string(zmq.SUBSCRIBE,unicode(""))
            self.sock.connect("tcp://localhost:" + str(self.memcache.getPubSubPort(self.sensorId)))
            self.memcache.incrementSubscriptionCount(sensorId)
            try :
                while True:
                    msg = self.sock.recv_pyobj()
                    if sensorId in msg:
                        msgdatabin = bitarray(msg[sensorId])
                        self.conn.send(msgdatabin.tobytes())
            except:
                print sys.exc_info()
                traceback.print_exc()
                print "Subscriber disconnected"
            finally:
                self.memcache.decrementSubscriptionCount(sensorId)

        except:
            tb = sys.exc_info()
            util.logStackTrace(tb)
        finally:
            if self.conn != None:
                self.conn.close()
            if self.sock != None:
                self.sock.close()
 
class OccupancyServer(threading.Thread):
    def __init__(self,socket):
        threading.Thread.__init__(self)
        self.socket = socket
              
        
    def run(self):
        while True:
            try :
                print "OccupancyServer: Accepting connections "
                (conn,addr) = self.socket.accept()
                if isSecure:
                    try :
                        cert = Config.getCertFile()
                        c = ssl.wrap_socket(conn,server_side = True, certfile = cert, ssl_version=ssl.PROTOCOL_SSLv3  )
                        t = OccupancyWorker(c)
                    except:
                        traceback.print_exc()
                        conn.close()
                        util.errorPrint("OccupancyServer: Error accepting connection")
                        util.logStackTrace(sys.exc_info())
                else:
                    t = OccupancyWorker(conn)
                util.debugPrint("OccupancyServer: Accepted a connection from "+str(addr))
                t.start()
            except:
                traceback.print_exc()  
                
if __name__ == "__main__" :
    occupancySock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    occupancyServerPort = Config.getOccupancyAlertPort()
    print "OccupancyServer: port = ", occupancyServerPort
    occupancySock.bind(('0.0.0.0',occupancyServerPort))
    occupancySock.listen(10)
    occupancyServer = OccupancyServer(occupancySock)
    occupancyServer.start()
                
import Config
import requests
import authentication
import sys
import traceback
import threading
import util
import flaskr as globals
from requests.exceptions import RequestException

# stores a table of peer keys generated randomly

peerSessionKeys = {}

class ConnectionMaintainer :
    def __init__ (self):
        self.peers = Config.getPeers()

    def start(self):
        if self.peers != None:
           threading.Timer(10.0, self.signIntoPeers).start()

    def signIntoPeers(self):
        #
        myHostName = Config.MY_HOST_NAME
        # re-start the timer ( do we need to stop first ?)
        threading.Timer(10.0,self.signIntoPeers).start()
        for peer in self.peers:
            if peer["host"] != myHostName:
                peerKey = peer["key"]
                peerProtocol = peer["protocol"]
                peerHost = peer["host"]
                peerPort = peer["port"]
                peerUrl = util.generateUrl(peerProtocol,peerHost,peerPort)
                peerSessionKey = authentication.generatePeerSessionKey()
                url = peerUrl + "/peerSignIn/" + Config.MY_SERVER_ID + "/" + peerKey
                try :
                    r = requests.post(url)
                    # Extract the returned token
                    if r.status_code == 200 :
                        jsonObj = r.json()
                        if jsonObj["status"] == "OK":
                            authentication.addSessionId(peerHost,peerSessionKey)
                            sessionKey = jsonObj["sessionId"]
                            if not peer in peerSessionKeys or sessionKey != peerSessionKeys[peer]:
                                peerSessionKeys[peer] = sessionKey
                                sensorIds = util.getMySensorIds()
                                for sensorId in sensorIds:
                                    self.registerSensorWithPeer(peerUrl,sensorId)
                        else:
                            util.debugPrint("Sign in with peer failed")
                except RequestException:
                     print "Unexpected error:", sys.exc_info()[0]
                     print sys.exc_info()
                     traceback.print_exc()
                     if peerHost in peerSessionKeys:
                         del peerSessionKeys[peerHost]

    def getPeerSessionKey(self,peerUrl):
        if peerUrl in peerSessionKeys:
            return peerSessionKeys[peerUrl]
        else:
            return None

    def registerSensorWithPeer(peer,sensorId):
        try :
            # first login to the peer. We need an account to login
            if Config.IS_SECURE :
                myBaseUrl = "https://" + Config.MY_HOSTNAME
            else:
                myBaseUrl = "http://" + Config.MY_HOSTNAME
            peerSessionKey = peerSessionKeys[peer]
            globals.session
            url = peer + "/registerSensorWithPeer/" + sensorId + "/" + peerSessionKey
            args = {"url":myBaseUrl}
            r = requests.post(url,args)
            jsonObj = r.json()
            if jsonObj["status"] != "OK":
                util.debugPrint("REGISTRATION of " + sensorId+ " with " + peer + " failed")
            else:
                util.debugPrint("REGISTRATION of " + sensorId+ " with " + peer + " succeded")
        except RequestException:
            print "Unexpected error:", sys.exc_info()[0]
            print sys.exc_info()
            traceback.print_exc()


def start() :
    ConnectionMaintainer().start()



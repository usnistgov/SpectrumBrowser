#! /usr/local/bin/python2.7
# -*- coding: utf-8 -*-
#
#This software was developed by employees of the National Institute of
#Standards and Technology (NIST), and others. 
#This software has been contributed to the public domain. 
#Pursuant to title 15 Untied States Code Section 105, works of NIST
#employees are not subject to copyright protection in the United States
#and are considered to be in the public domain. 
#As a result, a formal license is not needed to use this software.
# 
#This software is provided "AS IS."  
#NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
#OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
#MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
#AND DATA ACCURACY.  NIST does not warrant or make any representations
#regarding the use of the software or the results thereof, including but
#not limited to the correctness, accuracy, reliability or usefulness of
#this software.


import Config
import requests
import util
from requests.exceptions import RequestException
import GetLocationInfo
import memcache
import time
import json
import os
import MemCacheKeys

# stores a table of peer keys generated randomly
global peerSystemAndLocationInfo
global peerUrlMap

peerSystemAndLocationInfo = {}
peerUrlMap = {}


class ConnectionMaintainer:
    def __init__(self):
        self.mc = memcache.Client(['127.0.0.1:11211'], debug=0)
        self.myId = os.getpid()

    def readPeerSystemAndLocationInfo(self):
        global peerSystemAndLocationInfo
        locInfo = self.mc.get(MemCacheKeys.PEER_SYSTEM_AND_LOCATION_INFO)
        if locInfo is not None:
            peerSystemAndLocationInfo = locInfo

    def writePeerSystemAndLocationInfo(self):
        global peerSystemAndLocationInfo
        self.mc.set(MemCacheKeys.PEER_SYSTEM_AND_LOCATION_INFO,
                    peerSystemAndLocationInfo)

    def acquireSem(self):
        self.mc.add(MemCacheKeys.PEER_CONNECTION_MAINTAINER_SEM, self.myId)
        storedId = self.mc.get(MemCacheKeys.PEER_CONNECTION_MAINTAINER_SEM)
        if storedId == self.myId:
            return True
        else:
            return False

    def releaseSem(self):
        self.mc.delete(MemCacheKeys.PEER_CONNECTION_MAINTAINER_SEM)

    def start(self):
        while True:
            self.acquireSem()
            self.signIntoPeers()
            self.releaseSem()
            time.sleep(Config.getSoftStateRefreshInterval())

    def setPeerUrl(self, peerId, peerUrl):
        global peerUrlMap
        urlMap = self.mc.get(MemCacheKeys.PEER_URL_MAP)
        if urlMap is not None:
            peerUrlMap = urlMap
            peerUrlMap[peerId] = peerUrlMap
        self.mc.set(MemCacheKeys.PEER_URL_MAP, peerUrlMap)

    def readPeerUrlMap(self):
        urlMap = self.mc.get(MemCacheKeys.PEER_URL_MAP)
        if urlMap is not None:
            global peerUrlMap
            peerUrlMap = urlMap

    def signIntoPeers(self):
        global peerSystemAndLocationInfo
        # util.debugPrint("Starting peer sign in")
        myHostName = Config.getHostName()
        if myHostName is None:
            print "System not configured - returning"
            return
        # Load the cache
        self.readPeerUrlMap()
        self.readPeerSystemAndLocationInfo()
        inboundPeers = Config.getInboundPeers()
        for inboundPeer in inboundPeers:
            peerId = inboundPeer["PeerId"]
            if peerId in peerUrlMap:
                peerUrl = peerUrlMap[peerId]
                if peerUrl in peerSystemAndLocationInfo:
                    currentTime = time.time()
                    if currentTime - peerSystemAndLocationInfo[peerUrl]["_time"] > \
                        2 * Config.getSoftStateRefreshInterval():
                        del peerSystemAndLocationInfo[peerUrl]
        self.writePeerSystemAndLocationInfo()
        # re-start the timer ( do we need to stop first ?)
        self.peers = Config.getPeers()
        # If user authentication is required, we export nothing.
        if not Config.isAuthenticationRequired():
            for peer in self.peers:
                if peer["host"] != myHostName:
                    peerKey = Config.getServerKey()
                    peerProtocol = peer["protocol"]
                    peerHost = peer["host"]
                    peerPort = peer["port"]
                    myServerId = Config.getServerId()
                    peerUrl = util.generateUrl(peerProtocol, peerHost,
                                               peerPort)
                    currentTime = time.time()
                    self.readPeerSystemAndLocationInfo()
                    if peerUrl in peerSystemAndLocationInfo:
                        lastTime = peerSystemAndLocationInfo[peerUrl]["_time"]
                        if currentTime - lastTime < Config.getSoftStateRefreshInterval(
                        ) / 2:
                            continue
                    url = peerUrl + "/federated/peerSignIn/" + myServerId + "/" + peerKey
                    util.debugPrint("Peer URL = " + url)
                    locationInfo = GetLocationInfo.getLocationInfo()
                    postData = {}
                    try:
                        if locationInfo is not None:
                            postData["PublicPort"] = Config.getPublicPort()
                            postData["HostName"] = Config.getHostName()
                            postData["locationInfo"] = locationInfo
                            r = requests.post(url, data=json.dumps(postData))
                        else:
                            r = requests.post(url)
                        # Extract the returned token
                        if r.status_code == 200:
                            jsonObj = r.json()
                            if jsonObj["status"] == "OK":
                                if "locationInfo" in jsonObj:
                                    self.readPeerSystemAndLocationInfo()
                                    locationInfo = jsonObj["locationInfo"]
                                    locationInfo["_time"] = time.time()
                                    peerSystemAndLocationInfo[
                                        peerUrl] = locationInfo
                                    self.writePeerSystemAndLocationInfo()
                            else:
                                if peerUrl in peerSystemAndLocationInfo:
                                    del peerSystemAndLocationInfo[peerUrl]
                                util.debugPrint("Sign in with peer failed")
                        else:
                            util.debugPrint(
                                "Sign in with peer failed HTTP Status Code " +
                                str(r.status_code))
                    except RequestException:
                        print "Could not contact Peer at " + peerUrl
                        self.readPeerSystemAndLocationInfo()
                        if peerUrl in peerSystemAndLocationInfo:
                            del peerSystemAndLocationInfo[peerUrl]
                        self.writePeerSystemAndLocationInfo()

    def getPeerSystemAndLocationInfo(self):
        global peerSystemAndLocationInfo
        self.readPeerSystemAndLocationInfo()
        return peerSystemAndLocationInfo

    def setPeerSystemAndLocationInfo(self, url, systemAndLocationInfo):
        global peerSystemAndLocationInfo
        self.readPeerSystemAndLocationInfo()
        peerSystemAndLocationInfo[url] = systemAndLocationInfo
        self.writePeerSystemAndLocationInfo()


def start():
    global connectionMaintainer
    connectionMaintainer.start()


def getPeerSystemAndLocationInfo():
    global connectionMaintainer
    return connectionMaintainer.getPeerSystemAndLocationInfo()


def setPeerSystemAndLocationInfo(url, systemAndLocationInfo):
    systemAndLocationInfo["_time"] = time.time()
    connectionMaintainer.setPeerSystemAndLocationInfo(url,
                                                      systemAndLocationInfo)


def setPeerUrl(peerId, peerUrl):
    global connectionMaintainer
    connectionMaintainer.setPeerUrl(peerId, peerUrl)


def getPeerUrl(peerId):
    global connectionMaintainer
    connectionMaintainer.readPeerUrlMap()
    if peerId in peerUrlMap:
        return peerUrlMap[peerId]
    else:
        return None


if not "connectionMaintainer" in globals():
    connectionMaintainer = ConnectionMaintainer()

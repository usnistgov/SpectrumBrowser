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

# Keys for various things in memory cache.
# Put keys here and check for clashes.

PEER_SYSTEM_AND_LOCATION_INFO = "peerSystemAndLocationInfo"
PEER_CONNECTION_MAINTAINER_SEM = "peerConnectionMaintainerSem"
PEER_URL_MAP = "peerUrlMap"
RESOURCEKEYS_CPU = "CPU"
RESOURCEKEYS_VIRTMEM = "VirtMem"
RESOURCEKEYS_DISK = "Disk"
RESOURCEKEYS_NET_SENT = "NetSent"
RESOURCEKEYS_NET_RECV = "NetRecv"
RESOURCEKEYS = [RESOURCEKEYS_CPU, RESOURCEKEYS_VIRTMEM, RESOURCEKEYS_NET_SENT,
                RESOURCEKEYS_NET_RECV]

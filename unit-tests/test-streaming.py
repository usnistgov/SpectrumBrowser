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

from websocket import create_connection
import argparse
import binascii
import ssl

secure = False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process command line args")
    parser.add_argument("-data", help="File name to stream")
    args = parser.parse_args()
    filename = args.data
    if not secure:
        ws = create_connection("ws://127.0.0.1:8000/spectrumdb/stream")
    else:
        ws = create_connection("wss://localhost:8443/spectrumdb/stream",
                               sslopt=dict(cert_reqs=ssl.CERT_NONE))
    with open(filename, "r") as f:
        while True:
            bytes = f.read(64)
            toSend = binascii.b2a_base64(bytes)
            ws.send(toSend)

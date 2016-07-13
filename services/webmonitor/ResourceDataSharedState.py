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
'''
Created on Jul 13, 2015

@author: mdb4
'''
import memcache
import os


class MemCache:
    """
    Keeps a memory map of the data pushed by the resource streaming server so it is accessible
    by any of the flask worker processes.
    """

    def __init__(self):
        self.mc = memcache.Client(['127.0.0.1:11211'], debug=0)

    def getPID(self):
        return os.getpid()

    def loadResourceData(self, resource):
        key = str(resource).encode("UTF-8")
        resourcedata = self.mc.get(key)
        return resourcedata

    def setResourceData(self, resource, data):
        key = str(resource).encode("UTF-8")
        self.mc.set(key, data)

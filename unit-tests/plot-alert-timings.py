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
Created on Apr 1, 2015

@author: local
'''

import matplotlib.pyplot as plt


if __name__ == "__main__":
    plot = plt.figure(figsize=(6, 4))
    plt.xlabel("Background load (streams)")
    plt.ylabel("Alert timing (s)")
    load = []
    alertTiming = []
    alertStandardDeviation = []
    f = open("pulse-timing.out")
    while True:
        line = f.readline()
        if line is None or line == "":
            break
        pieces = line.split(",")
        load.append(int(pieces[0]))
        alertTiming.append(float(pieces[1]))
        alertStandardDeviation.append(float(pieces[2]))

    plt.scatter(load, alertTiming, marker='o')
    plt.errorbar(load,
                 alertTiming,
                 yerr=alertStandardDeviation,
                 linestyle="None")
    frame = plt.gca()
    # plt.errorbar(a,b,yerr=c, linestyle="None")
    # plt.errorbar(load,alertStandardDeviation)
    plt.savefig("load-test-timing.png", pad_inches=0, dpi=100)
    plt.clf()
    plt.close()

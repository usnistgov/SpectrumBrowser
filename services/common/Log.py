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
Created on Jun 3, 2015

@author: local
'''

import os
import util
import json
import DebugFlags
import logging
from flask import request
import Bootstrap

gwtSymbolMap = {}

global loggerName


def configureLogging(moduleName):
    loggerName = moduleName
    FORMAT = "%(levelname)s %(asctime)-15s %(message)s"
    if not logging.getLogger(loggerName).disabled:
        loglvl = DebugFlags.getLogLevel()
        logging.basicConfig(format=FORMAT,
                            level=loglvl,
                            filename=os.path.join(Bootstrap.getFlaskLogDir(),
                                                  moduleName + ".log"))


def getLogger():
    #global loggerName
    if not "loggerName" in globals():
        configureLogging("msod")
        return logging.getLogger("msod")
    else:
        return logging.getLogger(loggerName)


def load_symbol_map(symbolMapDir):
    files = [symbolMapDir + f for f in os.listdir(symbolMapDir)
             if os.path.isfile(symbolMapDir + f) and os.path.splitext(f)[1] ==
             ".symbolMap"]
    if len(files) != 0:
        symbolMap = files[0]
        symbolMapFile = open(symbolMap)
        lines = symbolMapFile.readlines()
        for line in lines:
            if line[0] == "#":
                continue
            else:
                pieces = line.split(',')
                lineNo = pieces[-2]
                fileName = pieces[-3]
                symbol = pieces[0]
                gwtSymbolMap[symbol] = {"file": fileName, "line": lineNo}


def loadGwtSymbolMap():
    symbolMapDir = util.getPath(
        "static/WEB-INF/deploy/spectrumbrowser/symbolMaps/")
    load_symbol_map(symbolMapDir)
    symbolMapDir = util.getPath("static/WEB-INF/deploy/admin/symbolMaps/")
    load_symbol_map(symbolMapDir)


def decodeStackTrace(stackTrace):
    lines = stackTrace.split()
    for line in lines:
        pieces = line.split(":")
        if pieces[0] in gwtSymbolMap:
            print gwtSymbolMap.get(pieces[0])
            file = gwtSymbolMap.get(pieces[0])["file"]
            lineNo = gwtSymbolMap.get(pieces[0])["line"]
            util.debugPrint(file + " : " + lineNo + " : " + pieces[1])


def log():
    if DebugFlags.debug:
        data = request.data
        jsonValue = json.loads(data)
        if "message" in jsonValue:
            message = jsonValue["message"]
        else:
            message = ""

        if "ExceptionInfo" in jsonValue:
            exceptionInfo = jsonValue["ExceptionInfo"]
        else:
            exceptionInfo = {}

        if len(exceptionInfo) != 0:
            util.errorPrint("Client Log Message : " + message)
            util.errorPrint("Client Exception Info:")
            for i in range(0, len(exceptionInfo)):
                util.errorPrint("Exception Message:")
                exceptionMessage = exceptionInfo[i]["ExceptionMessage"]
                util.errorPrint("Client Stack Trace :")
                stackTrace = exceptionInfo[i]["StackTrace"]
                util.errorPrint(exceptionMessage)
                decodeStackTrace(stackTrace)
            if "Traceback" in jsonValue:
                traceback = jsonValue["Traceback"]
                util.errorPrint("Traceback: " + traceback)
        else:
            util.debugPrint("Client Log Message : " + message)

    return "OK"

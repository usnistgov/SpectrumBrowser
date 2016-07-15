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

import msgutils
import numpy as np
import util
import matplotlib.pyplot as plt
import timezone
import os
import matplotlib as mpl
mpl.use('Agg')
import png
import sys
import gridfs
from bson.objectid import ObjectId
from json import dumps
import DbCollections
from Defines import TIME_ZONE_KEY, SENSOR_ID, \
    MINUTES_PER_DAY, SECONDS_PER_DAY, UNDER_CUTOFF_COLOR, \
    OVER_CUTOFF_COLOR, HOURS_PER_DAY, DATA_KEY, TIME, FREQ_RANGE, \
    STATUS, NOK, OK, ERROR_MESSAGE

from Defines import STATIC_GENERATED_FILE_LOCATION
from Defines import CHART_WIDTH
from Defines import CHART_HEIGHT
import DataMessage
import DebugFlags
import Config
import traceback


# get minute index offset from given time in seconds.
# startTime is the starting time from which to compute the offset.
def get_index(time, startTime):
    return int(float(time - startTime) / float(60))


def generateOccupancyForFFTPower(msg, fileNamePrefix):
    chWidth = Config.getScreenConfig()[CHART_WIDTH]
    chHeight = Config.getScreenConfig()[CHART_HEIGHT]

    measurementDuration = DataMessage.getMeasurementDuration(msg)
    nM = DataMessage.getNumberOfMeasurements(msg)
    n = DataMessage.getNumberOfFrequencyBins(msg)
    cutoff = DataMessage.getThreshold(msg)
    # miliSecondsPerMeasurement = float(measurementDuration * 1000) / float(nM)
    spectrogramData = msgutils.getData(msg)
    # Generate the occupancy stats for the acquisition.
    occupancyCount = [0 for i in range(0, nM)]
    for i in range(0, nM):
        occupancyCount[i] = float(len(filter(
            lambda x: x >= cutoff, spectrogramData[i, :]))) / float(n) * 100
    timeArray = [i for i in range(0, nM)]
    minOccupancy = np.minimum(occupancyCount)
    maxOccupancy = np.maximum(occupancyCount)
    plt.figure(figsize=(chWidth, chHeight))
    plt.axes([0, measurementDuration * 1000, minOccupancy, maxOccupancy])
    plt.xlim([0, measurementDuration])
    plt.plot(timeArray, occupancyCount, "g.")
    plt.xlabel("Time (s) since start of acquisition")
    plt.ylabel("Band Occupancy (%)")
    plt.title("Band Occupancy; Cutoff: " + str(cutoff))
    occupancyFilePath = util.getPath(
        STATIC_GENERATED_FILE_LOCATION) + fileNamePrefix + '.occupancy.png'
    plt.savefig(occupancyFilePath)
    plt.clf()
    plt.close()
    # plt.close('all')
    return fileNamePrefix + ".occupancy.png"


def generateSingleDaySpectrogramAndOccupancyForSweptFrequency(
        msg, sessionId, startTime, sys2detect, fstart,
        fstop, subBandMinFreq, subBandMaxFreq, cutoff):
    """
    Generate single day spectrogram and occupancy for SweptFrequency

    Parameters:

    - msg: the data message
    - sessionId: login session id.
    - startTime: absolute start time.
    - sys2detect: the system to detect.
    - fstart: start frequency.
    - fstop: stop frequency
    - subBandMinFreq: min freq of subband.
    - subBandMaxFreq: max freq of subband.
    - cutoff: occupancy threshold.

    """
    try:
        chWidth = Config.getScreenConfig()[CHART_WIDTH]
        chHeight = Config.getScreenConfig()[CHART_HEIGHT]

        locationMessage = msgutils.getLocationMessage(msg)
        tz = locationMessage[TIME_ZONE_KEY]
        startTimeUtc = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(
            startTime, tz)
        startMsg = DbCollections.\
            getDataMessages(msg[SENSOR_ID]).find_one(
                {SENSOR_ID:msg[SENSOR_ID], TIME:{"$gte":startTimeUtc},
                 FREQ_RANGE:msgutils.freqRange(sys2detect, fstart, fstop)})
        if startMsg is None:
            util.debugPrint("Not found")
            return {STATUS: NOK, ERROR_MESSAGE: "Data Not Found"}
        if DataMessage.getTime(startMsg) - startTimeUtc > SECONDS_PER_DAY:
            util.debugPrint("Not found - outside day boundary: " + str(
                startMsg['t'] - startTimeUtc))
            return {STATUS: NOK,
                    ERROR_MESSAGE: "Not found - outside day boundary."}

        msg = startMsg
        sensorId = msg[SENSOR_ID]
        powerValues = msgutils.trimSpectrumToSubBand(msg, subBandMinFreq,
                                                     subBandMaxFreq)
        vectorLength = len(powerValues)
        if cutoff is None:
            cutoff = DataMessage.getThreshold(msg)
        else:
            cutoff = int(cutoff)
        spectrogramFile = sessionId + "/" + sensorId + "." + str(
            startTimeUtc) + "." + str(cutoff) + "." + str(
                subBandMinFreq) + "." + str(subBandMaxFreq)
        spectrogramFilePath = util.getPath(
            STATIC_GENERATED_FILE_LOCATION) + spectrogramFile
        powerVal = np.array(
            [cutoff for i in range(0, MINUTES_PER_DAY * vectorLength)])
        spectrogramData = powerVal.reshape(vectorLength, MINUTES_PER_DAY)
        # artificial power value when sensor is off.
        sensorOffPower = np.transpose(np.array(
            [2000 for i in range(0, vectorLength)]))

        prevMessage = msgutils.getPrevAcquisition(msg)

        if DebugFlags.debug:
            util.debugPrint("First Data Message:")
            del msg["_id"]
            util.debugPrint(dumps(msg, indent=4))

        if prevMessage is None:
            util.debugPrint("prevMessage not found")
            prevMessage = msg
            prevAcquisition = sensorOffPower
        else:
            prevAcquisitionTime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(
                prevMessage['t'], tz)
            util.debugPrint("prevMessage[t] " + str(prevMessage[
                't']) + " msg[t] " + str(msg['t']) + " prevDayBoundary " + str(
                    prevAcquisitionTime))
            prevAcquisition = np.transpose(np.array(
                msgutils.trimSpectrumToSubBand(prevMessage, subBandMinFreq,
                                               subBandMaxFreq)))
        occupancy = []
        timeArray = []
        maxpower = -1000
        minpower = 1000
        # Note that we are starting with the first message.
        count = 1
        while True:
            acquisition = msgutils.trimSpectrumToSubBand(msg, subBandMinFreq,
                                                         subBandMaxFreq)
            occupancyCount = float(len(filter(lambda x: x >= cutoff,
                                              acquisition)))
            occupancyVal = occupancyCount / float(len(acquisition))
            occupancy.append(occupancyVal)
            minpower = np.minimum(minpower, msgutils.getMinPower(msg))
            maxpower = np.maximum(maxpower, msgutils.getMaxPower(msg))
            if prevMessage['t1'] != msg['t1']:
                # GAP detected so fill it with sensorOff
                sindex = get_index(
                    DataMessage.getTime(prevMessage), startTimeUtc)
                if get_index(
                        DataMessage.getTime(prevMessage), startTimeUtc) < 0:
                    sindex = 0
                for i in range(sindex, get_index(
                        DataMessage.getTime(msg), startTimeUtc)):
                    spectrogramData[:, i] = sensorOffPower
            elif DataMessage.getTime(prevMessage) > startTimeUtc:
                # Prev message is the same tstart and prevMessage is in the range of interest.
                # Sensor was not turned off.
                # fill forward using the prev acquisition.
                for i in range(get_index(DataMessage.getTime(prevMessage), startTimeUtc),
                               get_index(msg["t"], startTimeUtc)):
                    spectrogramData[:, i] = prevAcquisition
            else:
                # forward fill from prev acquisition to the start time
                # with the previous power value
                for i in range(0, get_index(
                        DataMessage.getTime(msg), startTimeUtc)):
                    spectrogramData[:, i] = prevAcquisition
            colIndex = get_index(DataMessage.getTime(msg), startTimeUtc)
            spectrogramData[:, colIndex] = acquisition
            timeArray.append(float(DataMessage.getTime(msg) - startTimeUtc) /
                             float(3600))
            prevMessage = msg
            prevAcquisition = acquisition
            msg = msgutils.getNextAcquisition(msg)
            if msg is None:
                lastMessage = prevMessage
                for i in range(
                        get_index(
                            DataMessage.getTime(prevMessage), startTimeUtc),
                        MINUTES_PER_DAY):
                    spectrogramData[:, i] = sensorOffPower
                break
            elif DataMessage.getTime(msg) - startTimeUtc >= SECONDS_PER_DAY:
                if msg['t1'] == prevMessage['t1']:
                    for i in range(
                            get_index(
                                DataMessage.getTime(prevMessage),
                                startTimeUtc), MINUTES_PER_DAY):
                        spectrogramData[:, i] = prevAcquisition
                else:
                    for i in range(
                            get_index(
                                DataMessage.getTime(prevMessage),
                                startTimeUtc), MINUTES_PER_DAY):
                        spectrogramData[:, i] = sensorOffPower

                lastMessage = prevMessage
                break
            count = count + 1

        # generate the spectrogram as an image.
        if not os.path.exists(spectrogramFilePath + ".png"):
            fig = plt.figure(figsize=(chWidth, chHeight))
            frame1 = plt.gca()
            frame1.axes.get_xaxis().set_visible(False)
            frame1.axes.get_yaxis().set_visible(False)
            cmap = plt.cm.spectral
            cmap.set_under(UNDER_CUTOFF_COLOR)
            cmap.set_over(OVER_CUTOFF_COLOR)
            dirname = util.getPath(STATIC_GENERATED_FILE_LOCATION) + sessionId
            if maxpower < cutoff:
                maxpower = cutoff
                minpower = cutoff
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            fig = plt.imshow(spectrogramData,
                             interpolation='none',
                             origin='lower',
                             aspect='auto',
                             vmin=cutoff,
                             vmax=maxpower,
                             cmap=cmap)
            util.debugPrint("Generated fig")
            plt.savefig(spectrogramFilePath + '.png',
                        bbox_inches='tight',
                        pad_inches=0,
                        dpi=100)
            plt.clf()
            plt.close()
        else:
            util.debugPrint("File exists - not generating image")

        util.debugPrint("FileName: " + spectrogramFilePath + ".png")

        util.debugPrint("Reading " + spectrogramFilePath + ".png")
        # get the size of the generated png.
        reader = png.Reader(filename=spectrogramFilePath + ".png")
        (width, height, pixels, metadata) = reader.read()

        util.debugPrint("width = " + str(width) + " height = " + str(height))

        # generate the colorbar as a separate image.
        if not os.path.exists(spectrogramFilePath + ".cbar.png"):
            norm = mpl.colors.Normalize(vmin=cutoff, vmax=maxpower)
            fig = plt.figure(figsize=(chWidth * 0.3, chHeight * 1.2))
            ax1 = fig.add_axes([0.0, 0, 0.1, 1])
            mpl.colorbar.ColorbarBase(ax1,
                                      cmap=cmap,
                                      norm=norm,
                                      orientation='vertical')
            plt.savefig(spectrogramFilePath + '.cbar.png',
                        bbox_inches='tight',
                        pad_inches=0,
                        dpi=50)
            plt.clf()
            plt.close()
        else:
            util.debugPrint(spectrogramFilePath + ".cbar.png" +
                            " exists -- not generating")

        localTime, tzName = timezone.getLocalTime(startTimeUtc, tz)

        # step back for 24 hours.
        prevAcquisitionTime = msgutils.getPrevDayBoundary(startMsg)
        nextAcquisitionTime = msgutils.getNextDayBoundary(lastMessage)
        meanOccupancy = np.mean(occupancy)
        maxOccupancy = np.max(occupancy)
        minOccupancy = np.min(occupancy)
        medianOccupancy = np.median(occupancy)

        result = {"spectrogram": Config.getGeneratedDataPath() + "/" + spectrogramFile + ".png",
                  "cbar":Config.getGeneratedDataPath() + "/" + spectrogramFile + ".cbar.png",
                  "maxPower":maxpower,
                  "maxOccupancy":maxOccupancy,
                  "minOccupancy":minOccupancy,
                  "meanOccupancy": meanOccupancy,
                  "medianOccupancy": medianOccupancy,
                  "cutoff":cutoff,
                  "aquisitionCount":count,
                  "minPower":minpower,
                  "tStartTimeUtc": startTimeUtc,
                  "timeDelta":HOURS_PER_DAY,
                  "prevAcquisition": prevAcquisitionTime,
                  "nextAcquisition": nextAcquisitionTime,
                  "formattedDate": timezone.formatTimeStampLong(startTimeUtc, tz),
                  "image_width":float(width),
                  "image_height":float(height)}

        result["timeArray"] = timeArray
        result["occupancyArray"] = occupancy
        if "ENBW" in lastMessage["mPar"]:
            enbw = lastMessage["mPar"]["ENBW"]
            result["ENBW"] = enbw

        if "RBW" in lastMessage["mPar"]:
            rbw = lastMessage["mPar"]["RBW"]
            result["RBW"] = rbw
        result[STATUS] = OK
        util.debugPrint(result)
        return result
    except:
        print "Unexpected error:", sys.exc_info()[0]
        print sys.exc_info()
        traceback.print_exc()
        util.logStackTrace(sys.exc_info())
        raise


# Generate a spectrogram and occupancy plot for FFTPower data starting at msg.
def generateSingleAcquisitionSpectrogramAndOccupancyForFFTPower(
        sensorId, sessionId, threshold, startTime, minFreq, maxFreq, leftBound,
        rightBound):
    util.debugPrint("generateSingleAcquisitionSpectrogramAndOccupancyForFFTPower " +
                    " sensorId = " + sensorId + " leftBound = " + str(leftBound) +
                    " rightBound = " + str(rightBound))
    dataMessages = DbCollections.getDataMessages(sensorId)
    chWidth = Config.getScreenConfig()[CHART_WIDTH]
    chHeight = Config.getScreenConfig()[CHART_HEIGHT]

    if dataMessages is None:
        return {STATUS: NOK, ERROR_MESSAGE: "Data message collection found "}
    msg = dataMessages.find_one({SENSOR_ID: sensorId, "t": startTime})
    if msg is None:
        return {STATUS: NOK,
                ERROR_MESSAGE:
                "No data message found at " + str(int(startTime))}
    if threshold is None:
        cutoff = DataMessage.getThreshold(msg)
    else:
        cutoff = int(threshold)
    startTime = DataMessage.getTime(msg)
    fs = gridfs.GridFS(DbCollections.getSpectrumDb(), msg[SENSOR_ID] + "_data")
    sensorId = msg[SENSOR_ID]
    messageBytes = fs.get(ObjectId(msg[DATA_KEY])).read()
    util.debugPrint("Read " + str(len(messageBytes)))
    spectrogramFile = sessionId + "/" + sensorId + "." + str(
        startTime) + "." + str(leftBound) + "." + str(rightBound) + "." + str(
            cutoff)
    spectrogramFilePath = util.getPath(
        STATIC_GENERATED_FILE_LOCATION) + spectrogramFile
    if leftBound < 0 or rightBound < 0:
        util.debugPrint("Bounds to exlude must be >= 0")
        return {STATUS: NOK, ERROR_MESSAGE: "Invalid bounds specified"}
    measurementDuration = DataMessage.getMeasurementDuration(msg)
    miliSecondsPerMeasurement = float(
        measurementDuration *
        1000) / float(DataMessage.getNumberOfMeasurements(msg))
    leftColumnsToExclude = int(leftBound / miliSecondsPerMeasurement)
    rightColumnsToExclude = int(rightBound / miliSecondsPerMeasurement)
    if leftColumnsToExclude + rightColumnsToExclude >= DataMessage.getNumberOfMeasurements(
            msg):
        util.debugPrint("leftColumnToExclude " + str(leftColumnsToExclude) +
                        " rightColumnsToExclude " + str(rightColumnsToExclude))
        return {STATUS: NOK, ERROR_MESSAGE: "Invalid bounds"}
    util.debugPrint("LeftColumns to exclude " + str(leftColumnsToExclude) +
                    " right columns to exclude " + str(rightColumnsToExclude))

    noiseFloor = DataMessage.getNoiseFloor(msg)
    nM = DataMessage.getNumberOfMeasurements(
        msg) - leftColumnsToExclude - rightColumnsToExclude
    n = DataMessage.getNumberOfFrequencyBins(msg)
    locationMessage = msgutils.getLocationMessage(msg)
    lengthToRead = n * DataMessage.getNumberOfMeasurements(msg)
    # Read the power values
    power = msgutils.getData(msg)
    powerVal = np.array(power[n * leftColumnsToExclude:lengthToRead - n *
                              rightColumnsToExclude])
    minTime = float(leftColumnsToExclude *
                    miliSecondsPerMeasurement) / float(1000)
    spectrogramData = powerVal.reshape(nM, n)
    maxpower = msgutils.getMaxPower(msg)
    if maxpower < cutoff:
        maxpower = cutoff
    # generate the spectrogram as an image.
    if (not os.path.exists(spectrogramFilePath + ".png")) or\
       DebugFlags.getDisableSessionIdCheckFlag():
        dirname = util.getPath(STATIC_GENERATED_FILE_LOCATION) + sessionId
        if not os.path.exists(dirname):
            os.makedirs(util.getPath(STATIC_GENERATED_FILE_LOCATION) +
                        sessionId)
        fig = plt.figure(figsize=(chWidth, chHeight))  # aspect ratio
        frame1 = plt.gca()
        frame1.axes.get_xaxis().set_visible(False)
        frame1.axes.get_yaxis().set_visible(False)
        cmap = plt.cm.spectral
        cmap.set_under(UNDER_CUTOFF_COLOR)
        fig = plt.imshow(
            np.transpose(spectrogramData),
            interpolation='none',
            origin='lower',
            aspect="auto",
            vmin=cutoff,
            vmax=maxpower,
            cmap=cmap)
        util.debugPrint("Generated fig " + spectrogramFilePath + ".png")
        plt.savefig(spectrogramFilePath + '.png',
                    bbox_inches='tight',
                    pad_inches=0,
                    dpi=100)
        plt.clf()
        plt.close()
    else:
        util.debugPrint("File exists -- not regenerating")

    # generate the occupancy data for the measurement.
    occupancyCount = [0 for i in range(0, nM)]
    for i in range(0, nM):
        occupancyCount[i] = float(len(filter(
            lambda x: x >= cutoff, spectrogramData[i, :]))) / float(n)
    timeArray = [int((i + leftColumnsToExclude) * miliSecondsPerMeasurement)
                 for i in range(0, nM)]

    # get the size of the generated png.
    reader = png.Reader(filename=spectrogramFilePath + ".png")
    (width, height, pixels, metadata) = reader.read()

    if (not os.path.exists(spectrogramFilePath + ".cbar.png")) or \
       DebugFlags.getDisableSessionIdCheckFlag():
        # generate the colorbar as a separate image.
        norm = mpl.colors.Normalize(vmin=cutoff, vmax=maxpower)
        fig = plt.figure(figsize=(chWidth * 0.2,
                                  chHeight * 1.22))  # aspect ratio
        ax1 = fig.add_axes([0.0, 0, 0.1, 1])
        mpl.colorbar.ColorbarBase(ax1,
                                  cmap=cmap,
                                  norm=norm,
                                  orientation='vertical')
        plt.savefig(spectrogramFilePath + '.cbar.png',
                    bbox_inches='tight',
                    pad_inches=0,
                    dpi=50)
        plt.clf()
        plt.close()

    nextAcquisition = msgutils.getNextAcquisition(msg)
    prevAcquisition = msgutils.getPrevAcquisition(msg)

    if nextAcquisition is not None:
        nextAcquisitionTime = DataMessage.getTime(nextAcquisition)
    else:
        nextAcquisitionTime = DataMessage.getTime(msg)

    if prevAcquisition is not None:
        prevAcquisitionTime = DataMessage.getTime(prevAcquisition)
    else:
        prevAcquisitionTime = DataMessage.getTime(msg)

    tz = locationMessage[TIME_ZONE_KEY]

    timeDelta = DataMessage.getMeasurementDuration(msg) - float(
        leftBound) / float(1000) - float(rightBound) / float(1000)

    meanOccupancy = np.mean(occupancyCount)
    maxOccupancy = np.max(occupancyCount)
    minOccupancy = np.min(occupancyCount)
    medianOccupancy = np.median(occupancyCount)

    result = {"spectrogram": Config.getGeneratedDataPath() + "/" + spectrogramFile + ".png",
              "cbar":Config.getGeneratedDataPath() + "/" + spectrogramFile + ".cbar.png",
              "maxPower":maxpower,
              "cutoff":cutoff,
              "noiseFloor": noiseFloor,
              "minPower":msgutils.getMinPower(msg),
              "maxFreq":DataMessage.getFmax(msg),
              "minFreq":DataMessage.getFmin(msg),
              "minTime": minTime,
              "timeDelta": timeDelta,
              "measurementsPerAcquisition":DataMessage.getNumberOfMeasurements(msg),
              "binsPerMeasurement": DataMessage.getNumberOfFrequencyBins(msg),
              "measurementCount": nM,
              "maxOccupancy": maxOccupancy,
              "minOccupancy": minOccupancy,
              "meanOccupancy": meanOccupancy,
              "medianOccupancy": medianOccupancy,
              "currentAcquisition":DataMessage.getTime(msg),
              "prevAcquisition": prevAcquisitionTime,
              "nextAcquisition": nextAcquisitionTime,
              "formattedDate": timezone.formatTimeStampLong(DataMessage.getTime(msg), tz),
              "image_width":float(width),
              "image_height":float(height)}
    # Now put in the occupancy data
    result[STATUS] = OK
    util.debugPrint(
        "generateSingleAcquisitionSpectrogramAndOccupancyForFFTPower:returning (abbreviated): " + str(result))
    result["timeArray"] = timeArray
    result["occupancyArray"] = occupancyCount

    return result

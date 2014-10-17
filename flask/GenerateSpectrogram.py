
import msgutils
import numpy as np
import util
import matplotlib.pyplot as plt
import flaskr as main
import timezone
import populate_db
from flask import request,abort,jsonify
import os
import matplotlib as mpl
mpl.use('Agg')
import png
import sys
import gridfs
from bson.objectid import ObjectId


# get minute index offset from given time in seconds.
# startTime is the starting time from which to compute the offset.
def getIndex(time, startTime) :
    return int (float(time - startTime) / float(60))


def generateOccupancyForFFTPower(msg, fileNamePrefix):
    measurementDuration = msg["mPar"]["td"]
    nM = msg['nM']
    n = msg['mPar']['n']
    cutoff = msg['cutoff']
    miliSecondsPerMeasurement = float(measurementDuration * 1000) / float(nM)
    spectrogramData = msgutils.getData(msg)
    # Generate the occupancy stats for the acquisition.
    occupancyCount = [0 for i in range(0, nM)]
    for i in range(0, nM):
        occupancyCount[i] = util.roundTo3DecimalPlaces(float(len(filter(lambda x: x >= cutoff, spectrogramData[i, :]))) / float(n) * 100)
    timeArray = [i * miliSecondsPerMeasurement for i in range(0, nM)]
    minOccupancy = np.minimum(occupancyCount)
    maxOccupancy = np.maximum(occupancyCount)
    plt.figure(figsize=(6, 4))
    plt.axes([0, measurementDuration * 1000, minOccupancy, maxOccupancy])
    plt.xlim([0, measurementDuration * 1000])
    plt.plot(timeArray, occupancyCount, "g.")
    plt.xlabel("Time (ms) since start of acquisition")
    plt.ylabel("Band Occupancy (%)")
    plt.title("Band Occupancy; Cutoff : " + str(cutoff))
    occupancyFilePath = util.getPath("static/generated/") + fileNamePrefix + '.occupancy.png'
    plt.savefig(occupancyFilePath)
    plt.clf()
    plt.close()
    # plt.close('all')
    return  fileNamePrefix + ".occupancy.png"




def generateSingleDaySpectrogramAndOccupancyForSweptFrequency(msg, sessionId, startTime, fstart, fstop, subBandMinFreq, subBandMaxFreq):
    try :
        locationMessage = msgutils.getLocationMessage(msg)
        tz = locationMessage[main.TIME_ZONE_KEY]
        startTimeUtc = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(startTime, tz)
        startMsg = main.db.dataMessages.find_one({main.SENSOR_ID:msg[main.SENSOR_ID], "t":{"$gte":startTimeUtc}, \
                "freqRange":populate_db.freqRange(fstart, fstop)})
        if startMsg == None:
            util.debugPrint("Not found")
            abort(404)
        if startMsg['t'] - startTimeUtc > main.SECONDS_PER_DAY:
            util.debugPrint("Not found - outside day boundary")
            abort(404)

        msg = startMsg
        sensorId = msg[main.SENSOR_ID]
        noiseFloor = msg["wnI"]
        powerValues = msgutils.trimSpectrumToSubBand(msg, subBandMinFreq, subBandMaxFreq)
        vectorLength = len(powerValues)
        cutoff = int(request.args.get("cutoff", msg['cutoff']))
        spectrogramFile = sessionId + "/" + sensorId + "." + str(startTimeUtc) + "." + str(cutoff) + "." + str(subBandMinFreq) + "." + str(subBandMaxFreq)
        spectrogramFilePath = util.getPath("static/generated/") + spectrogramFile
        powerVal = np.array([cutoff for i in range(0, main.MINUTES_PER_DAY * vectorLength)])
        spectrogramData = powerVal.reshape(vectorLength, main.MINUTES_PER_DAY)
        # artificial power value when sensor is off.
        sensorOffPower = np.transpose(np.array([2000 for i in range(0, vectorLength)]))

        prevMessage = msgutils.getPrevAcquisition(msg)

        if prevMessage == None:
            util.debugPrint ("prevMessage not found")
            prevMessage = msg
            prevAcquisition = sensorOffPower
        else:
            prevAcquisitionTime = timezone.getDayBoundaryTimeStampFromUtcTimeStamp(prevMessage['t'], tz)
            util.debugPrint ("prevMessage[t] " + str(prevMessage['t']) + " msg[t] " + str(msg['t']) + " prevDayBoundary " + str(prevAcquisitionTime))
            prevAcquisition = np.transpose(np.array(msgutils.trimSpectrumToSubBand(prevMessage, subBandMinFreq, subBandMaxFreq)))
        occupancy = []
        timeArray = []
        maxpower = -1000
        minpower = 1000
        while True:
            acquisition = msgutils.trimSpectrumToSubBand(msg, subBandMinFreq, subBandMaxFreq)
            minpower = np.minimum(minpower, msg['minPower'])
            maxpower = np.maximum(maxpower, msg['maxPower'])
            if prevMessage['t1'] != msg['t1']:
                 # GAP detected so fill it with sensorOff
                print "Gap generated"
                for i in range(getIndex(prevMessage["t"], startTimeUtc), getIndex(msg["t"], startTimeUtc)):
                    spectrogramData[:, i] = sensorOffPower
            elif prevMessage["t"] > startTimeUtc:
                # Prev message is the same tstart and prevMessage is in the range of interest.
                # Sensor was not turned off.
                # fill forward using the prev acquisition.
                for i in range(getIndex(prevMessage['t'], startTimeUtc), getIndex(msg["t"], startTimeUtc)):
                    spectrogramData[:, i] = prevAcquisition
            else :
                # forward fill from prev acquisition to the start time
                # with the previous power value
                for i in range(0, getIndex(msg["t"], startTimeUtc)):
                    spectrogramData[:, i] = prevAcquisition
            colIndex = getIndex(msg['t'], startTimeUtc)
            spectrogramData[:, colIndex] = acquisition
            timeArray.append(float(msg['t'] - startTimeUtc) / float(3600))
            occupancy.append(util.roundTo1DecimalPlaces(msg['occupancy']))
            prevMessage = msg
            prevAcquisition = acquisition
            msg = msgutils.getNextAcquisition(msg)
            if msg == None:
                lastMessage = prevMessage
                for i in range(getIndex(prevMessage["t"], startTimeUtc), main.MINUTES_PER_DAY):
                    spectrogramData[:, i] = sensorOffPower
                break
            elif msg['t'] - startTimeUtc > main.SECONDS_PER_DAY:
                for i in range(getIndex(prevMessage["t"], startTimeUtc), main.MINUTES_PER_DAY):
                    spectrogramData[:, i] = prevAcquisition
                lastMessage = prevMessage
                break

        # generate the spectrogram as an image.
        if not os.path.exists(spectrogramFilePath + ".png"):
           fig = plt.figure(figsize=(6, 4))
           frame1 = plt.gca()
           frame1.axes.get_xaxis().set_visible(False)
           frame1.axes.get_yaxis().set_visible(False)
           cmap = plt.cm.spectral
           cmap.set_under(main.UNDER_CUTOFF_COLOR)
           cmap.set_over(main.OVER_CUTOFF_COLOR)
           dirname = util.getPath("static/generated/") + sessionId
           if not os.path.exists(dirname):
              os.makedirs(dirname)
           fig = plt.imshow(spectrogramData, interpolation='none', origin='lower', aspect='auto', vmin=cutoff, vmax=maxpower, cmap=cmap)
           print "Generated fig"
           plt.savefig(spectrogramFilePath + '.png', bbox_inches='tight', pad_inches=0, dpi=100)
           plt.clf()
           plt.close()
        else:
           util.debugPrint("File exists - not generating image")

        util.debugPrint("FileName : " + spectrogramFilePath + ".png")

        util.debugPrint("Reading " + spectrogramFilePath + ".png")
        # get the size of the generated png.
        reader = png.Reader(filename=spectrogramFilePath + ".png")
        (width, height, pixels, metadata) = reader.read()

        util.debugPrint("width = " + str(width) + " height = " + str(height))

        # generate the colorbar as a separate image.
        if not os.path.exists(spectrogramFilePath + ".cbar.png") :
          norm = mpl.colors.Normalize(vmin=cutoff, vmax=maxpower)
          fig = plt.figure(figsize=(4, 10))
          ax1 = fig.add_axes([0.0, 0, 0.1, 1])
          mpl.colorbar.ColorbarBase(ax1, cmap=cmap, norm=norm, orientation='vertical')
          plt.savefig(spectrogramFilePath + '.cbar.png', bbox_inches='tight', pad_inches=0, dpi=50)
          plt.clf()
          plt.close()
        else:
          util.debugPrint(spectrogramFilePath + ".cbar.png" + " exists -- not generating")


        localTime, tzName = timezone.getLocalTime(startTimeUtc, tz)

        # step back for 24 hours.
        prevAcquisitionTime = msgutils.getPrevDayBoundary(startMsg)
        nextAcquisitionTime = msgutils.getNextDayBoundary(lastMessage)


        result = {"spectrogram": spectrogramFile + ".png", \
            "cbar":spectrogramFile + ".cbar.png", \
            "maxPower":maxpower, \
            "cutoff":cutoff, \
            "noiseFloor" : noiseFloor, \
            "minPower":minpower, \
            "tStartTimeUtc": startTimeUtc, \
            "timeDelta":main.HOURS_PER_DAY, \
            "prevAcquisition" : prevAcquisitionTime , \
            "nextAcquisition" : nextAcquisitionTime , \
            "formattedDate" : timezone.formatTimeStampLong(startTimeUtc, tz), \
            "image_width":float(width), \
            "image_height":float(height)}

        util.debugPrint(result)
        result["timeArray"] = timeArray
        result["occupancyArray"] = occupancy
        return jsonify(result)
    except  :
         print "Unexpected error:", sys.exc_info()[0]
         raise

# Generate a spectrogram and occupancy plot for FFTPower data starting at msg.
def generateSingleAcquisitionSpectrogramAndOccupancyForFFTPower(msg, sessionId):
    startTime = msg['t']
    fs = gridfs.GridFS(main.db, msg[main.SENSOR_ID] + "/data")
    sensorId = msg[main.SENSOR_ID]
    messageBytes = fs.get(ObjectId(msg["dataKey"])).read()
    util.debugPrint("Read " + str(len(messageBytes)))
    cutoff = int(request.args.get("cutoff", msg['cutoff']))
    leftBound = float(request.args.get("leftBound", 0))
    rightBound = float(request.args.get("rightBound", 0))
    spectrogramFile = sessionId + "/" + sensorId + "." + str(startTime) + "." + str(leftBound) + "." + str(rightBound) + "." + str(cutoff)
    spectrogramFilePath = util.getPath("static/generated/") + spectrogramFile
    if leftBound < 0 or rightBound < 0 :
        util.debugPrint("Bounds to exlude must be >= 0")
        return None
    measurementDuration = msg["mPar"]["td"]
    miliSecondsPerMeasurement = float(measurementDuration * 1000) / float(msg['nM'])
    leftColumnsToExclude = int(leftBound / miliSecondsPerMeasurement)
    rightColumnsToExclude = int(rightBound / miliSecondsPerMeasurement)
    if leftColumnsToExclude + rightColumnsToExclude >= msg['nM']:
        util.debugPrint("leftColumnToExclude " + str(leftColumnsToExclude) + " rightColumnsToExclude " + str(rightColumnsToExclude))
        return None
    util.debugPrint("LeftColumns to exclude " + str(leftColumnsToExclude) + " right columns to exclude " + str(rightColumnsToExclude))
    noiseFloor = msg['wnI']
    nM = msg["nM"] - leftColumnsToExclude - rightColumnsToExclude
    n = msg["mPar"]["n"]
    locationMessage = msgutils.getLocationMessage(msg)
    lengthToRead = n * msg["nM"]
    # Read the power values
    power = msgutils.getData(msg)
    powerVal = power[n * leftColumnsToExclude:lengthToRead - n * rightColumnsToExclude]
    minTime = float(leftColumnsToExclude * miliSecondsPerMeasurement) / float(1000)
    spectrogramData = powerVal.reshape(nM, n)
    maxpower = msg['maxPower']
    if maxpower < cutoff:
       maxpower = cutoff
    # generate the spectrogram as an image.
    if not os.path.exists(spectrogramFilePath + ".png"):
       dirname = util.getPath("static/generated/") + sessionId
       if not os.path.exists(dirname):
           os.makedirs(util.getPath("static/generated/") + sessionId)
       fig = plt.figure(figsize=(6, 4))
       frame1 = plt.gca()
       frame1.axes.get_xaxis().set_visible(False)
       frame1.axes.get_yaxis().set_visible(False)
       cmap = plt.cm.spectral
       cmap.set_under(main.UNDER_CUTOFF_COLOR)
       fig = plt.imshow(np.transpose(spectrogramData), interpolation='none', origin='lower', aspect="auto", vmin=cutoff, vmax=maxpower, cmap=cmap)
       util.debugPrint("Generated fig")
       plt.savefig(spectrogramFilePath + '.png', bbox_inches='tight', pad_inches=0, dpi=100)
       plt.clf()
       plt.close()
    else :
       util.debugPrint("File exists -- not regenerating")

    # generate the occupancy data for the measurement.
    occupancyCount = [0 for i in range(0, nM)]
    for i in range(0, nM):
        occupancyCount[i] = util.roundTo1DecimalPlaces(float(len(filter(lambda x: x >= cutoff, spectrogramData[i, :]))) / float(n) * 100)
    timeArray = [int((i + leftColumnsToExclude) * miliSecondsPerMeasurement)  for i in range(0, nM)]

    # get the size of the generated png.
    reader = png.Reader(filename=spectrogramFilePath + ".png")
    (width, height, pixels, metadata) = reader.read()

    if not os.path.exists(spectrogramFilePath + ".cbar.png"):
       # generate the colorbar as a separate image.
       norm = mpl.colors.Normalize(vmin=cutoff, vmax=maxpower)
       fig = plt.figure(figsize=(4, 10))
       ax1 = fig.add_axes([0.0, 0, 0.1, 1])
       mpl.colorbar.ColorbarBase(ax1, cmap=cmap, norm=norm, orientation='vertical')
       plt.savefig(spectrogramFilePath + '.cbar.png', bbox_inches='tight', pad_inches=0, dpi=50)
       plt.clf()
       plt.close()

    nextAcquisition = msgutils.getNextAcquisition(msg)
    prevAcquisition = msgutils.getPrevAcquisition(msg)

    if nextAcquisition != None:
        nextAcquisitionTime = nextAcquisition['t']
    else:
        nextAcquisitionTime = msg['t']

    if prevAcquisition != None:
        prevAcquisitionTime = prevAcquisition['t']
    else:
        prevAcquisitionTime = msg['t']

    tz = locationMessage[main.TIME_ZONE_KEY]

    timeDelta = msg["mPar"]["td"] - float(leftBound) / float(1000) - float(rightBound) / float(1000)

    result = {"spectrogram": spectrogramFile + ".png", \
            "cbar":spectrogramFile + ".cbar.png", \
            "maxPower":maxpower, \
            "cutoff":cutoff, \
            "noiseFloor" : noiseFloor, \
            "minPower":msg['minPower'], \
            "maxFreq":msg["mPar"]["fStop"], \
            "minFreq":msg["mPar"]["fStart"], \
            "minTime": minTime, \
            "timeDelta": timeDelta, \
            "prevAcquisition" : prevAcquisitionTime , \
            "nextAcquisition" : nextAcquisitionTime , \
            "formattedDate" : timezone.formatTimeStampLong(msg['t'] + leftBound , tz), \
            "image_width":float(width), \
            "image_height":float(height)}
    # Now put in the occupancy data
    result["timeArray"] = timeArray
    result["occupancyArray"] = occupancyCount
    return jsonify(result)


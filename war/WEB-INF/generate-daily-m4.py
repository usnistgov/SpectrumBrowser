import matplotlib.pyplot as plt
import numpy as np
import argparse
import csv
import time

def get_bin_from_freq(freq, min_freq, max_freq, nchannels):
    delta = float(max_freq - min_freq)/float(nchannels)
    bin = int(float(freq - min_freq)/delta)
    return bin


parser = argparse.ArgumentParser(description='Process command line args')
parser.add_argument('-f',help='spectrogram power array')
parser.add_argument('-g',help='gaps in the spectrogram')
parser.add_argument('-min_freq',help='min freq')
parser.add_argument('-max_freq',help='max_freq')
parser.add_argument('-L', help = 'power limit')
args = parser.parse_args()

# fetch the args.
spectrogramFile = args.f


min_power = int (args.L)
gaps = args.g
min_freq = int (args.min_freq)
max_freq = int (args.max_freq)

rows = -1
cols = -1

# open spectrogram file as a csv file
csvfile = open(spectrogramFile)
csvreader = csv.reader(csvfile)

# figure out how many rows and columns we have.
csvfile = open(spectrogramFile)
csvr = csv.reader(csvfile)
for line in csvr :
        row = int(line[0])
        col = int(line[1])
        if row > rows :
            rows = row
        if col > cols:
            cols = col

gapcsvfile = open(gaps)
gapscsvr = csv.reader(gapcsvfile)
for line in gapscsvr:
    col = int(line[1])
    if col > cols :
        cols = col

rows = rows + 1
cols = cols + 1
print rows, cols

# Each row is one sweep.
nchannels = rows

# open spectrogram file as a csv file
csvfile = open(spectrogramFile)
csvreader = csv.reader(csvfile)

mintime = time.time()*1000.0
maxtime = 0

#print rows, cols
print "rows = ", rows , " cols = ", cols
csvfile = open(spectrogramFile)
csvr = csv.reader(csvfile)
powermap = {}
times = []
for line in csvr :
        freq = int(line[4])
        time = int(line[3])
        power = float(line[2])
        if time < mintime:
            mintime = time
        if time > maxtime:
            maxtime = time
        times.append(time)
        powerList = powermap.get(freq,None)
        if powerList == None:
            powerList = []
            powerList.append(power)
            powermap[freq] = powerList
        else:
            powerList.append(power)

csvfile.close()

normalized_time = []
milisec_per_day = 24*60*60*1000
for time in times:
    normalized_time.append(time - mintime)


# sort and eliminate duplicates
sorted_times = np.unique(normalized_time)

median=[]
mean=[]
max=[]
min=[]

freqs = np.sort(powermap.keys())
for key in freqs:
    powerList = powermap[key]
    median.append(np.median(powerList))
    mean.append(np.mean(powerList))
    max.append(np.amax(powerList))
    min.append(np.amin(powerList))

plt.plot(freqs,median,freqs,mean,freqs,max,freqs,min)
plt.legend(['Median','Mean','Max','Min'], loc='upper right')
plt.xlabel('Frequency (MHz)')
plt.ylabel('Power (dBm)')
#plt.show()
plt.title('M4 Statistics')
plt.savefig(spectrogramFile + '-m4.png')
plt.close()


delta = (max_freq - min_freq)/nchannels

timeIndex = {}

# prepare the array.
#print sorted_times
for time in sorted_times:
    timeIndex[time] = []

csvfile = open(spectrogramFile)
csvr = csv.reader(csvfile)
for line in csvr :
        freq = int(line[4])
        time = int(line[3])
        power = float(line[2])
        bin_list = timeIndex.get(time - mintime,None)
        if power >= min_power :
            bin_list.append(get_bin_from_freq(freq,min_freq,max_freq,nchannels))


occupancy = []
for time in sorted_times:
    bin_list = timeIndex.get(time,None)
    bin_list_sorted = np.unique(bin_list)
    percentOccupancy = float(len(bin_list_sorted))/float(nchannels) * float(100)
    occupancy.append(percentOccupancy)

mean_occupancy = np.mean(occupancy)

hourly_mean = []
miliseconds_per_hour = 60*60*1000

for i in range(len(occupancy)):
    sum = occupancy[i]
    j = i+1
    count = 1
    while j < len(sorted_times) and sorted_times[j] - sorted_times[i] < miliseconds_per_hour :
        sum = sum + occupancy[j]
        j = j + 1
        count = count + 1
    hourly_mean.append(float(sum) / float(count))


plt.plot(sorted_times, occupancy,'rx',sorted_times,hourly_mean,'--')
plt.legend(['measurement','hourly mean'], loc='upper right')
plt.xlabel("Hours")
plt.ylabel("Occupancy ")
plt.title("Band Occupancy : " + str(min_freq)  +  "<= f <= " + str(max_freq) + " MHz; Mean = " +  \
    str(round(mean_occupancy,2)) + "%\n Cutoff = " + str(min_power) + " dBm " + " Channel Count " + str(nchannels))
plt.xticks([i for i in range(0,milisec_per_day,milisec_per_day/24)])
xticklabels = ["%d" % i for i in range(0,24,1)]
ax = plt.gca()
ax.xaxis.set_ticklabels(xticklabels)
ax.set_xlim([0,milisec_per_day])
ax.set_ylim([0,100])
plt.savefig(spectrogramFile + '-occupancy.png')




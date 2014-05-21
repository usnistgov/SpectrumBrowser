import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import argparse
import csv
import time 
from mpl_toolkits.axes_grid1 import make_axes_locatable


parser = argparse.ArgumentParser(description='Process command line args')
parser.add_argument('-f',help='spectrogram power array')
parser.add_argument('-g',help='gaps in the spectrogram')
parser.add_argument('-min_freq',help='min freq')
parser.add_argument('-max_freq',help='max_freq')
parser.add_argument('-min_power',help='min_power')
parser.add_argument('-image-width', help = 'image-width')
parser.add_argument('-image-height', help = 'image-height')

args = parser.parse_args()
spectrogramFile = args.f
gaps = args.g
#TODO -- pass these in.
image_width = 800
image_height = 402
minfreq = int (args.min_freq)
maxfreq = int (args.max_freq)
power_cutoff = float(args.min_power)

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
spectrogramData =  None
#-100 is the floor of the data
minpower = 100000
maxpower = -100000
floor = float(-100)
ciel = float(10)

#initialize the 2-d array with the floor values
t = [[floor  for j in range(cols)] for i in range(rows)]

spectrogramData = np.array(t,float)

#now deal with the gaps.
gapcsvfile = open(gaps)
gapscsvr = csv.reader(gapcsvfile)
for line in gapscsvr:
    gapStartTime = int(line[0])
    gapEndTime = int(line[1])
    for j in range(gapStartTime,gapEndTime):
        for i in range(rows):
            # set it to a value above the max
            spectrogramData[i][j] = ciel

# now populate the array with the spectrum power values.
csvfile = open(spectrogramFile)
csvr = csv.reader(csvfile)
for line in csvr :
        freq = int(line[0])
        time = int(line[1])
        power = float(line[2])
        if power < power_cutoff:
            #Threshold the values.
            power = floor
        else:
            if power < minpower:
                minpower = power
            if power > maxpower:
                maxpower = power
        rowindex = freq
        colindex = time
        spectrogramData[rowindex ][colindex ] =  float(power)



plt.ylabel("Frequency (mHz)")
plt.xlabel("Hours")

ax = plt.gca()

plt.xticks(range(0,image_width,image_width/24))
xticklabels = ["%d" % i for i in range(0,24,1)]
ax.xaxis.set_ticklabels(xticklabels)

plt.yticks(range(0,image_height,image_height/5))
yticklabels=["%d" %i for i in range(minfreq,maxfreq,(maxfreq-minfreq)/5)]
ax.yaxis.set_ticklabels(yticklabels)

fig = plt.imshow(spectrogramData,interpolation='nearest', extent=[0,image_width,0,image_height], aspect=1,vmin=minpower,vmax=maxpower)

#cmap = plt.cm.gist_ncar_r
cmap = plt.cm.spectral
cmap.set_under('white')
cmap.set_over('black')
norm = mpl.colors.Normalize(vmin=minpower, vmax=maxpower)
fig.set_cmap(cmap)

divider = make_axes_locatable(ax)
cax = divider.append_axes("right", size="5%", pad=0.05)

plt.colorbar(fig, cax=cax)

#plt.savefig(spectrogramFile + '.png',  bbox_inches='tight', pad_inches=0.125, dpi=50)

plt.savefig(spectrogramFile + '.png')

print "Done!"
#plt.show()

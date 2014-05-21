import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import argparse
import csv
import time 
from matplotlib.path import Path
import matplotlib.patches as patches


parser = argparse.ArgumentParser(description='Process command line args')
parser.add_argument('-f',help='spectrogram power array')
parser.add_argument('-g',help='gaps in the spectrogram')
args = parser.parse_args()
spectrogramFile = args.f
gaps = args.g
image_width = 800
image_height = 402

# open spectrogram file as a csv file
csvfile = open(spectrogramFile)
csvreader = csv.reader(csvfile)

spectrogramData =  None
#-100 is the floor of the data

rows = -1
cols = -1
minpower = 100000
maxpower = -100000
floor = float(-100)

# find the min and max time and frequency in the range.
for line in csvreader :
    row = int(line[0])
    column = int(line[1])
    if row > rows :
        rows = row
    if column > cols :
        cols = column
    power = float(line[2])
    if power < minpower:
        minpower = power
    if power > maxpower:
        maxpower = power

#now deal with the gaps.
gapcsvfile = open(gaps)
gapscsvr = csv.reader(gapcsvfile)
for line in gapscsvr:
    gapStartTime = int(line[0])
    gapEndTime = int(line[1])
    if gapEndTime > cols :
        cols = gapEndTime


cols = cols + 1
rows = rows + 1

print "rows = ", rows , " cols = ", cols

t = [[floor  for j in range(cols)] for i in range(rows)]

spectrogramData = np.array(t,float)


csvfile = open(spectrogramFile)
csvr = csv.reader(csvfile)
for line in csvr :
        freq = int(line[0])
        time = int(line[1])
        power = float(line[2])
        rowindex = freq
        colindex = time
        spectrogramData[rowindex ][colindex ] =  float(power)
        if power < minpower:
            minpower = power
        if power > maxpower:
            maxpower = power

#now deal with the gaps.
gapcsvfile = open(gaps)
gapscsvr = csv.reader(gapcsvfile)
for line in gapscsvr:
    gapStartTime = int(line[0])
    gapEndTime = int(line[1])
    for j in range(gapStartTime,gapEndTime):
        for i in range(rows):
            spectrogramData[i][j] = float(10)

#print spectrogramData
frame1 = plt.gca()
frame1.axes.get_xaxis().set_visible(False)
frame1.axes.get_yaxis().set_visible(False)


fig = plt.imshow(spectrogramData,interpolation='nearest', extent=[0,image_width,0,image_height], aspect=1,vmin=minpower,vmax=maxpower)



#cmap = plt.cm.gist_ncar_r
cmap = plt.cm.spectral
cmap.set_under('white')
cmap.set_over('black')
fig.set_cmap(cmap)
plt.savefig(spectrogramFile + '.png', bbox_inches='tight', pad_inches=0, dpi=50)

# draw the colorbar
a = np.array([minpower,maxpower])
#print a
norm = mpl.colors.Normalize(vmin=minpower, vmax=maxpower)
fig = plt.figure(figsize=(4,10))
ax1 = fig.add_axes([0.0, 0, 0.1, 1])
cb1 = mpl.colorbar.ColorbarBase(ax1, cmap=cmap, norm=norm, orientation='vertical')
plt.savefig(spectrogramFile + 'cbar.png', bbox_inches='tight', pad_inches=0, dpi=50)

#plt.show()



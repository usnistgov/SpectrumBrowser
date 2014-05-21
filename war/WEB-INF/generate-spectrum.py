import matplotlib.pyplot as plt
import argparse
import csv
import datetime
import pytz


parser = argparse.ArgumentParser(description='Process command line args')
parser.add_argument('-f',help='spectrogram power array')
parser.add_argument('-t', help = 'time')
parser.add_argument('-tz', help = 'timezone')


args = parser.parse_args()

csvfile = args.f
t = int(args.t)
tz = args.tz
title = "Spectrum for " + str(datetime.datetime.fromtimestamp(float(t)/1000.0,tz=pytz.timezone(tz)))
#title = "Spectrum for " + str(datetime.datetime.fromtimestamp(float(t)/1000.0))

csvreader = csv.reader(open(csvfile))
power=[]
freq=[]

for line in csvreader:
    freq.append(int(line[0]))
    power.append(int(line[1]))

plt.plot(freq,power)
plt.title(title)
plt.xlabel("Frequency (MHz)")
plt.ylabel("Power (dBm)")
#plt.show()
plt.savefig(csvfile + '.png')

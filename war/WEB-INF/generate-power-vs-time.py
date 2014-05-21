import matplotlib.pyplot as plt
import argparse
import csv
import datetime
import pytz

def get_date(timestamp,tz):
    dt = datetime.datetime.fromtimestamp(timestamp,tz)
    return str(dt.year) + "-" + str(dt.month) + "-" + str(dt.day)

parser = argparse.ArgumentParser(description='Process command line args')
parser.add_argument('-f',help='spectrogram power array')
parser.add_argument('-tz',help='time zone')
parser.add_argument('-freq',help='frequency')

args = parser.parse_args()

csvfile = args.f
tz =  args.tz
freq = args.freq
title = "Power vs. Time. Frequency = " + str(freq) + " MHz."

csvreader = csv.reader(open(csvfile))
power=[]
time=[]

for line in csvreader:
    time.append(float(line[0])/1000.0)
    power.append(int(line[1]))

mintime = int (time[0])
maxtime = int (time[len(time) -1])

plt.plot(time,power)
plt.xlabel("Date")
plt.ylabel("Power (dBm)")

ax = plt.gca()
xticklabels  = []
locs =  ax.xaxis.get_majorticklocs()
for t in locs:
    xticklabels.append(get_date(t,pytz.timezone(tz)))
ax.xaxis.set_ticklabels(xticklabels)
plt.title(title)
plt.savefig(csvfile + '.png')
#plt.show()
print "Done"



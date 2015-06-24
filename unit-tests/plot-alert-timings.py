'''
Created on Apr 1, 2015

@author: local
'''
import matplotlib as mpl

import matplotlib.pyplot as plt


if __name__=="__main__":
     plot = plt.figure(figsize=(6, 4))
     plt.xlabel("Background load (streams)")
     plt.ylabel("Alert timing (s)")
     load = []
     alertTiming = []
     alertStandardDeviation = []
     f = open("pulse-timing.out")
     while True:
         line = f.readline()
         if line == None or line == "" :
             break
         pieces = line.split(",")
         load.append(int(pieces[0]))
         alertTiming.append(float(pieces[1]))
         alertStandardDeviation.append(float(pieces[2]))
    
     plt.scatter(load,alertTiming,marker='o')
     plt.errorbar(load,alertTiming,yerr=alertStandardDeviation,linestyle="None")
     frame = plt.gca()
     #plt.errorbar(a,b,yerr=c, linestyle="None")
     #plt.errorbar(load,alertStandardDeviation)
     plt.savefig("load-test-timing.png", pad_inches=0, dpi=100)
     plt.clf()
     plt.close()    

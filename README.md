<h1> The D.O.C. Spectrum Monitoring Project </h1>

The purpose of this project is to provide a database for registering sensor readings. A user of the database will be able to pick a frequency
band of interest and explore the data readings etc...(words to be added).

This is a joint effort between the NIST and NTIA.

<h2> How to build and run it. </h2>

<h3> Dependencies </h3>

Download and install the following tools and dependencies. Set up your PATH, CLASSPATH, LD_LIBRARY_PATH and PYTHONPATH as instructed. (Ask if you need 
 to know what my settings are):

     Python 2.7 https://www.python.org/
     SciPy www.scipy.org (includes numpy, matplotlib)
     mongodb http://www.mongodb.org/downloads
     JDK 1.7 http://www.oracle.com/technetwork/java/javase/downloads/jdk7-downloads-1880260.html
     Google Web Toolkit  2.6.1 http://www.gwtproject.org/download.html
     Ant http://ant.apache.org/
     Flask http://flask.pocoo.org/
     pymongo  ( you can install this using pip install but you will need to install pip first )

<h3> Operating Systems </h3>

I have only tested on Linux (Centos 6.5) thus far but should work on Windows 7 ( volunteers needed ).

<h3> Build it </h3>

    cd SpectrumBrowser
    ant

<h3> Run it </h3>

 Populate the database. I will assume you are using a unix shell. If you are using a Windows Shell, please use equivalent commands.

    cd SpectrumBrowser/flask

    mkdir -p data/db

    mongodb -dbpath data/db
    (wait till it initializes and announces that it is ready for accepting connections)

    cd SpectrumBrowser/flask/data

    python populate_db.py -data LTE_UL_bc17_ts103b.dat

    This will run for a while ( about 5 minutes)

    cd SpectrumBrowser/flask

    python flaskr.py

point your browser at http://localhost:5000
Log in as guest (no password).


<h2> NOTE </h2>

This project (including this page) is in an early state of development. 

<h2>Copyrights and disclaimers </h2>
Standard NIST public domain disclaimer goes here.

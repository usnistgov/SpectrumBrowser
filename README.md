<h1> The D.O.C. Spectrum Monitoring Project </h1>

The purpose of this project is to provide a database for registering sensor readings. A user of the database will be able to pick a frequency
band of interest and explore the data readings etc...(words to be added).

This is a joint effort between NIST (EMNTG) and NTIA (ITS).

<h2> How to build and run it. </h2>

<h3> Dependencies </h3>

Download and install the following tools and dependencies. Set up your PATH and PYTHONPATH as needed. 
(Ask mranga@nist.gov for installation help as needed):

     Python 2.7 https://www.python.org/
     pip https://pypi.python.org/pypi/pip
     SciPy www.scipy.org (includes numpy, matplotlib - download and install for your OS)
     mongodb http://www.mongodb.org/downloads
     JDK 1.7 http://www.oracle.com/technetwork/java/javase/downloads/jdk7-downloads-1880260.html
     Google Web Toolkit  2.6.1 http://www.gwtproject.org/download.html
     Ant http://ant.apache.org/
     Flask http://flask.pocoo.org/ (you will need to install dependencies that flask needs)
     pymongo  https://pypi.python.org/pypi/pymongo/ (pip install pymongo)
     pypng  https://github.com/drj11/pypng (pip install pypng)
     pytz   http://pytz.sourceforge.net/ (pip install pytz)
     pyopenssl https://github.com/pyca/pyopenssl (pip install pyopenssl)

     Dependencies Install Notes:
     You will need numpy 1.5.1 or higher. Get it from sourceforge and build and install it.
     You will need the latest version of matplotlib get it from github and build and install it.
     I like to put all my python packages under a directory called $HOME/.python
     When you go to install werkzeug (which is a flask dependency), you will need to specify
     pip install -t $HOME/.python/lib/python2.6/site-packages

     My PYTHONPATH has the following.
     $HOME/.python/lib/python2.6/site-packages/ AND $HOME/.python/usr/lib/python2.6/site-packages/ $HOME/.python/usr/lib64/python2.6/site-packages

<h3> Operating Systems </h3>

My development platform is  Linux (Centos 6.5) thus far but should work on Windows 7 (volunteers needed).

<h3> Build it </h3>

The GWT_HOME environment variable should point to where you have gwt installed.

    cd SpectrumBrowser
    ant

The default ant target will compile the client side code and generate javascript. Currently it is only 
set up to optimize code for firefox (restriction will be removed in production).

<h3> Run it </h3>

First populate the database (you only have to do this once). 
I will assume you are using a unix shell. If you are using a Windows Shell, please use equivalent commands.
Feel free to update the instructions.

Start the mongo database server

    cd SpectrumBrowser/flask
    mkdir -p data/db
    mongodb -dbpath data/db
    (wait till it initializes and announces that it is ready for accepting connections)

Populate the DB with test data (I am using the LTE data as an example for test purposes)

    cd SpectrumBrowser/flask
    python populate_db.py -data data/LTE_UL_bc17_ts103b.dat
    This will run for a while ( about 5 minutes)
    (this file is not on github - too big. Ask mranga@nist.gov for data files when you are ready for this step.)

Start the development web server (only supports http)

    cd SpectrumBrowser/flask
    python flaskr.py

point your browser at http://localhost:5000
Log in as guest (no password).


<h2> LIMITATIONS </h2>

There are several limitations at present. Here are a few :

This project (including this page) is in an early state of development.
Currently, I am only generating client side JavaScript for Firefox and Chrome (in order to save development time).
The final version will remove this restriction and generate code for Firefox, Chrome, Opera and IE-9. 
There is no https support for the development web server. We will add https support using an apache httpd front end.

<h2>Copyrights and disclaimers </h2>
Python and scipy copyrights and acknowledgements will go here.
Standard NIST public domain disclaimer goes here.

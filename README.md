<h2> The DOC Spectrum Monitoring Project </h2>

The purpose of this project is to provide a database and graphical tools
for recording and examining spectrum measurements.  The primary audience
for this project is researchers and policy makers who have an interest
in knowing how the spectrum is being utilized in various frequency bands
around the United States. Our initial focus is on the LTE and Radar bands.
A user of this project  will be able to pick a frequency band of interest
and explore the data readings etc...(words to be added).

This is a joint effort between NIST (EMNTG) and NTIA (ITS).

<h2> How to build and run it using Docker. </h2>

1. [Install Docker for your platform and start it](http://docs.docker.com/installation/) - following instructions to get the newest version available (ONLY ONCE)
2. `sudo gpasswd -a ${USER} docker` (ONLY ONCE)
3. `sudo service docker restart` (or equivelent for your OS) (ONLY ONCE)
4. `docker login --username="ntiaits" --password="2/;8J3s>E->G0Um"` (alternately, create your own Docker Hub account and send your username to danderson@its.bldrdoc.gov and I'll add you to the organization "institute4telecomsciences" which has access to our private docker repo. This step will be unnecessary when we publish our code.
5. `docker run -d --name mongodb_data -v /data/db busybox` (create a minimal "data storage container" for our server to save persistent data to)
6. `DB_PID=$(docker run -d --volumes-from mongodb_data --name mongodb ntiaits/mongodb)` (Start MongoDB and point it at our persistent storage container)
7. Populate some test DB data (THIS IS UNTESTED, IT WILL LOOK SOMETHING LIKE THIS:) `DATA=/path/to/LTE_data.dat; CDATA=/tmp/$(basename $DATA); docker run -it --rm --link mongodb:db -v $DATA:$CDATA ntiaits/spectrumbrowser-server python populate_db.py -data $CDATA`
7. `SERVER_PID=$(docker run -d -p 8000:8000 --name sbserver --link mongodb:db ntiaits/spectrumbrowser-server)` (run the server and link it to our MongoDB container)
8. Now type `0.0.0.0:8000` into your browser. You should have a live server.

Some other things to try:
```    
docker logs mongodb/sbserver
docker start/stop/restart mongodb/sbserver
# (For debugging--start an interactive term in the container. DON'T automatically start mongod and flask)
docker run -tip 8000:8000 --rm --link mongodb:db ntiaits/spectrumbrowser-server /bin/bash
# After making changes (on the host), build a new image:
cd $SPECTRUM_BROWSER_HOME
docker build -t ntiaits/spectrumbrowser-server .
# Test it out
# If it looks good, push it so everyone else can use your changes
docker push ntiaits/spectrumbrowser-server

```
    
Email danderson@its.bldrdoc.gov with any issues you have with the docker image.

*NOTE:* This is a work in progress. Currently we can start the server, but not logon, because I don't have any data in the database. There are a few things left todo:

**Docker image TODO**
- [ ] Reduce size of docker image (currently the build process is pulling in Xorg and many deps we don't use)
- [ ] Work out best way to get data into the container (network port? docker volume? docker "link"?)

<h2> How to build and run it manually. </h2>

Set the SPECTRUM_BROWSER_HOME environment variable to the location in your file system where
this file is checked out (i.e. the project root). Under centos you can do this as follows:

All paths in the following instructions are with relative to SPECTRUM_BROWSER_HOME.


    export SPECTRUM_BROWSER_HOME=/path/to/project

<h3> Dependencies </h3>

This project is based heavily on Python, Mongodb and GWT.

Download and install the following tools and dependencies. Set up your PATH and PYTHONPATH as needed. 
(Ask mranga@nist.gov for installation help as needed):

     Python 2.7 https://www.python.org/
     pip https://pypi.python.org/pypi/pip
     SciPy www.scipy.org (includes numpy, matplotlib - download and install for your OS)
     mongodb http://www.mongodb.org/downloads
     Ant http://ant.apache.org/
     Flask http://flask.pocoo.org/ (you will need to install dependencies that flask needs)
     pymongo  https://pypi.python.org/pypi/pymongo/ (pip install pymongo)
     pypng  https://github.com/drj11/pypng (pip install pypng)
     pytz   http://pytz.sourceforge.net/ (pip install pytz)
     pyopenssl https://github.com/pyca/pyopenssl (pip install pyopenssl)
     gevent python co-routines  (pip install gevent)
     flask_websockets websocket support for flask  (pip install Flask-Sockets) 
     websockets (python websocket client) https://github.com/liris/websocket-client   (pip install websockets)


     JDK 1.7 http://www.oracle.com/technetwork/java/javase/downloads/jdk7-downloads-1880260.html

     Google Web Toolkit  2.6.1 http://www.gwtproject.org/download.html
     
     agg - the antigrain aliasing backend for matplotlib png generation. For centos or fedora yum install agg.

     Dependencies Install Notes:
     You will need numpy 1.5.1 or higher. Get it from sourceforge and build and install it.
     You will need the latest version of matplotlib get it from github and build and install it.
     I like to put all my python packages under a directory called $HOME/.python. You may want to put local packages
     in $HOME/.local in which case you can do pip localinstall where ever pip install is specified above.
     If you put your python packages in .python when you go to install werkzeug 
     (which is a flask dependency), you will need to specify
     pip install -t $HOME/.python/lib/python2.6/site-packages

     My PYTHONPATH has the following.
     $HOME/.python/lib/python2.6/site-packages/ AND $HOME/.python/usr/lib/python2.6/site-packages/ $HOME/.python/usr/lib64/python2.6/site-packages

     Depending on where you put things, you may need to modify your PYTHONPATH accordingly.

<h3> Operating Systems </h3>

My development platform is  Linux (Centos 6.5) thus far but should work on Windows 7 (volunteers needed).
Streaming support will only work on a system that supports websockets for wsgi. This currently only works on 
Linux Ngnix so the httpd server is likely to be replaced with Ngnix. If you do not need live sensor streaming,
then you should be fine installing on Windows.

<h3> Build it </h3>

The GWT_HOME environment variable should point to where you have gwt installed.

    cd SpectrumBrowser
    ant

The default ant target will compile the client side code and generate javascript. Currently it is only 
set up to optimize code for firefox (restriction will be removed in production).

<h3> Run it </h3>


Populate the database (you only have to do this once). 
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

point your browser at http://localhost:8000
Log in as guest (no password).


<h2> LIMITATIONS </h2>

There are several limitations at present. Here are a few :

This project (including this page) is in an early state of development.

BUGS are not an optional feature. They come bundled with the software
at no extra cost.

Testing testing and more testing is needed. Please report bugs and suggestions.

Under development, I am only generating client side JavaScript
optimized for Firefox and Chrome (in order to save development
time).  The final version will remove this restriction and
generate code for Firefox, Chrome, Opera and IE-9.  Modify
src/gov/nist/spectrumbrowser/SpectrumBrowser.gwt.xml to remove this
limitation before compiling.

There is no https support for the development web server (bundled with
flask).  For HTTPS support, you need to run the production Apache httpd
web server. See configuration instructions in the httpd directory.



<h2>Copyrights and disclaimers </h2>
Python and scipy copyrights and acknowledgements will go here.
Standard NIST public domain disclaimer goes here.

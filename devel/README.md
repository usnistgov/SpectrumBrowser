<h1> Build Instructions </h1>

<h2> Set up your environment </h2>

Set the SPECTRUM_BROWSER_HOME environment variable to the location in your file system where
this file is checked out (i.e. the project root). Under centos you can do this as follows:

All paths in the following instructions are with relative to SPECTRUM_BROWSER_HOME.


    export SPECTRUM_BROWSER_HOME=/path/to/project

<h2> How to build and run it using Docker </h2>

[Install Docker for your platform and start it](http://docs.docker.com/installation/) - following instructions to get the newest version available.

All following `docker` commands assume you've added yourself to the `docker` group. (Do this only once per install)
```bash
sudo gpasswd -a ${USER} docker
((you need to log out and back in for group changes to take effect))
sudo service docker restart
```

For now, the Docker repo is private and requires login. If you set up your own Docker Hub account, send your username to danderson@its.bldrdoc.gov and I'll add you to the organization "institute4telecomsciences" which also has access to the ntiaits private repo.
```bash
docker login --username="ntiaits" --password="2/;8J3s>E->G0Um"
```

This is where the magic happens: **1)** create a persistant data container (otherwise we lose our data when we restart the mongo container) **2)** Start a container running MongoDB and point it at the container created in step #1, and **3)** start the Spectrum Browser server and "link" it to the MongoDB containers. That's it!
```bash
docker run -d --name mongodb_data -v /data/db busybox
docker run -d --volumes-from mongodb_data --name mongodb ntiaits/mongodb
docker run -d -p 8000:8000 --name sbserver --link mongodb:db ntiaits/spectrumbrowser-server
```

**NOTE: the `ntiaits/spectrumbrowser-server` image currently sits at around 1.5GB... go get a coffee while it's downloading for the first time.**

Now type `0.0.0.0:8000` into your browser. You should have a live server!

If you're using `boot2docker` on Windows of Mac, you will probably also need to tell VirtualBox to forward ports to the host:

```bash
VBoxManage controlvm boot2docker-vm natpf1 "sbserver,tcp,127.0.0.1,8000,,8000"
```

You may need to populate some test DB data. If so, stop any running `sbserver` containers and run this, modifying `/path/to/LTE_data.dat` to the file on your host system. **(I haven't tested this yet, just leaving this here as a draft)**
```bash
DAT=/path/to/LTE_data.dat; CONTAINER_DAT=/tmp/$(basename $DAT); docker run -it --rm --link mongodb:db -v $DAT:$CONTAINER_DAT ntiaits/spectrumbrowser-server python populate_db.py -data $CONTAINER_DAT
```

Some other things to try:
```bash
docker logs mongodb
docker restart sbserver
# (For debugging--this will start an interactive term in the container without starting Flask.)
docker run -tip 8000:8000 --rm --link mongodb:db ntiaits/spectrumbrowser-server /bin/bash
```

And finally, if you make changes to code affecting the server, feel free to rebuild the image and push it out!
```bash
cd $SPECTRUM_BROWSER_HOME
docker build -t ntiaits/spectrumbrowser-server .
docker push ntiaits/spectrumbrowser-server
```

<h3>Troubleshooting Docker</h3>

On Ubuntu, Docker can sometimes fail to forward your Internet connection into containers because Ubuntu uses NetworkManager to dynamically manage some network information. If you see network-related errors, try manually informing Docker about your DNS servers.
```bash
# We'll first look up our current DNS server addresses with
# NetworkManager tool (nm-tool)
$ nm-tool |grep DNS
    DNS:             ###.###.###.###
    DNS:             ###.###.###.###
# Now add the following line in /etc/default/docker
DOCKER_OPTS="--dns ###.###.###.### --dns ###.###.###.###"
# Restart the docker server
$ sudo service docker restart
# If you were building, tell Docker to disregard its cache and try again
$ docker build --no-cache -t ntiaits/spectrumbrowser-server .
```

Email danderson@its.bldrdoc.gov with any issues you have with the Docker image.

<h2> How to build and run it manually. </h2>


<h3> Dependencies </h3>

This project is based heavily on Python, Mongodb and GWT.

Download and install the following tools and dependencies. Set up your PATH and PYTHONPATH as needed.
Where-ever pip install is indicated below, you can use the --user flag to install under $HOME/.local
(Ask mranga@nist.gov for installation help as needed):

     Python 2.7 https://www.python.org/
     pip https://pypi.python.org/pypi/pip

     JDK 1.7 http://www.oracle.com/technetwork/java/javase/downloads/jdk7-downloads-1880260.html

     Google Web Toolkit  2.6.1 http://www.gwtproject.org/download.html
     Note that we are using gwt-2.6.1 and not gwt-2.7.0 ( there are some issues with gwt-2.7.0)

     The mongodb version should be 2.6.5 or newer
     mongodb http://www.mongodb.org/downloads

     Ant http://ant.apache.org/

     nginx web server http://nginx.org/download

     The following is optional but will greatly simplify your life:
     pip install virtalenv
     pip install virtualenvwrapper


     Your OS install may already include a few of these packages:
     I am assuming you are running on Centos, Fedora or RedHat and are using yum for
     package management (use equivalent commands eg. "apt" for other flavors of Linux):

     You can install all the following OS dependencies at once by running sh devel/yum-install.sh

     If you don't want to work in batch mode, here are the OS dependencies:
     yum group install "C Development Tools and Libraries"
     openssl: sudo yum install openssl
     openssl-devel: sudo yum install openssl-devel
     libffi:  sudo yum install libffi
     libffi-devel: sudo yum install libffi-devel
     libpng:  sudo yum install libpbg
     libpng-devel: sudo yum install libpng-devel
     freetype:  sudo yum install freetype
     freetype-devel:  sudo yum install freetype
     libevent: yum install libevent
     libevent-devel: yum install libevent-devel
     agg: yum install agg
     memcached: yum install memcached
     gtk2-devel: yum install gtk2-devel


     Assuming you took my advice and installed virtualenv, now define a
     virtualenv in which you do your python installs so you won't need to be root
     or do local installs for your python packages:
     mkvirtualenv sb
     workon sb



     Now proceed to install python depenencies:
     You can install all these dependencies at once by using

     pip install -r requirements.txt --user

     Here are the dependencies:

     SciPy www.scipy.org (includes numpy, matplotlib - download and install for your OS or individually)
     maplotlib: pip install matplotlib
     numpy: pip install numpy
     Flask http://flask.pocoo.org/ (pip install flask)
     CORS extension https://pypi.python.org/pypi/Flask-Cors  (pip install flask-CORS)
     pymongo  https://pypi.python.org/pypi/pymongo/ (pip install pymongo)
     pypng  https://github.com/drj11/pypng (pip install pypng)
     pytz   http://pytz.sourceforge.net/ (pip install pytz)
     pyopenssl https://github.com/pyca/pyopenssl (pip install pyopenssl)
     gevent python co-routines  (pip install gevent)
     flask_websockets websocket support for flask  (pip install Flask-Sockets)
     websockets (python websocket client) https://github.com/liris/websocket-client (pip install websocket-client)
     gunicorn (python wsgi server)  http://gunicorn.org/
     sphinx document generation tool (pip install sphinx)
     sphinx autohttp contrib (pip install sphinxcontrib-httpdomain)
     python-memcached wrapper for memcache. https://github.com/linsomniac/python-memcached (pip install python-memcache)
     requests HTTP requests package for python  (pip install requests)


     Dependencies Install Notes:
     The --user flag puts things in  .local under your $HOME.

     If you are not using virtualenv for your install, set up your PYTHONPATH environment variable
     according to where your python packages were installed. For example:
     $HOME/.local/lib/python2.6/site-packages/ AND $HOME/.local/usr/lib/python2.6/site-packages/ $HOME/.local/usr/lib64/python2.6/site-packages



<h3> Operating Systems </h3>

My development platform is  Linux (Centos 6.5) thus far but should work on Windows 7 (volunteers needed).
Streaming support will only work on a system that supports websockets for wsgi. This currently only works on
Linux Ngnix so the httpd server is likely to be replaced with Ngnix. If you do not need live sensor streaming,
then you should be fine installing on Windows. Also with Windows, you cannot run gunicorn and hence your server
will consist of a single flask worker process, resulting in bad performance for multi-user access.

<h3> Build it </h3>

The GWT_HOME environment variable should point to where you have gwt installed.
The SPECTRUM_BROWSER_HOME variable should point to where you have git cloned the installation.

    cd $SPECTRUM_BROWSER_HOME
    ant

The default ant target will compile the client side code and generate javascript. Under development, it is only
set up to optimize code for firefox. To remove this restriction use:

   ant demo

but it will take longer to compile.

<h3> Run it </h3>


Populate the database (you only have to do this once).
I will assume you are using a unix shell. If you are using a Windows Shell, please use equivalent commands.
Feel free to update the instructions.

Start the mongo database server

    cd $SPECTRUM_BROWSER_HOME/flask
    mkdir -p data/db
    sh start-db.sh
    (wait till it initializes and announces that it is ready for accepting connections)

Populate the DB with test data (I am using the LTE data as an example for test purposes)

    cd $SPECTRUM_BROWSER_HOME/flask
    python populate_db.py -data data/LTE_UL_bc17_ts106_p2.dat
    This will run for a while ( about 5 minutes)
    (this file is not on github - too big. Ask mranga@nist.gov for data files when you are ready for this step.)

If you have populated the DB with data that corresponds to a previous version of MSOD (> MSOD-06), then upgrade the data using

    python upgrade-db.py

For debugging, start the development web server (only supports http and only one Flask worker)

    cd $SPECTRUM_BROWSER_HOME/flask
    python flaskr.py

OR for multi-worker support (better throughput)

   sh start-gunicorn.sh

Configure the system

    Point your browser at localhost:8000
    The default admin password in admin.

Browse the data

   point your browser at http://localhost:8000

<h3> Stopping the system</h3>

To stop the database

   sh stop-db.sh

To stop flask

   sh stop-gunicorn.sh


<h2> LIMITATIONS </h2>

There are several limitations at present. Here are a few :

This project (including this page) is in an early state of development.

BUGS are not an optional feature. They come bundled with the software
at no extra cost.

Testing testing and more testing is needed. Please report bugs and suggestions.
Use the issue tracker on github to report issues.

For HTTPS support, you need to run the production Nginx httpd
web server. See configuration instructions in the httpd directory.

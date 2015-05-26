
<h1> Build Instructions </h1>

<h2> Deploy system using install_stack.sh and Makefile </h2>

```bash
# Clone the SpectrumBrowser repo. /opt will be the preferred location for deployment systems
# but any location should be correctly handled.
$ cd /opt && sudo git clone https://<+GITHUB_USERNAME+>@github.com/usnistgov/SpectrumBrowser.git
$ sudo groupadd --system spectrumbrowser
$ sudo useradd --system spectrumbrowser -g spectrumbrowser
$ sudo chown --recursive spectrumbrowser:spectrumbrowser /opt/SpectrumBrowser
$ sudo chmod --recursive g+w /opt/SpectrumBrowser/
$ sudo usermod --append --groups spectrumbrowser $(whoami)
# Log out of the VM and back in. You should see "spectrumbrowser" when you type groups:
$ groups
danderson wheel spectrumbrowser
# You can now work in /opt/SpectrumBrowser without sudo, including git pull, etc.

# Change directory into the repository root after cloning/pulling
$ cd SpectrumBrowser
# Install the software stack
$ cd devel
$ sudo ./install_stack.sh
# Follow instructions to log out and back in if GWT was not previously installed
$ cd -
# Edit the DB_PORT_27017_TCP_ADDR field in /opt/SpectrumBrowser/MSODConfig.json
# The default target runs "ant" and the install target installs and/or modifies 
# config files for nginx, gunicorn, and flask
$ make && sudo make install
# To build the "demo" target
$ make demo && sudo make install
```
<h2> Run Services </h2>
```bash
# Monitor log files:
$ tail -f /var/log/gunicorn/*.log -f /var/log/flask/*.log -f /var/log/nginx/*.log -f /var/log/memcached.log
# Start service scripts
$ sudo service memcached start # (also available: stop/status)
$ sudo service nginx start # (also available: stop/status)
# There is not currently a service script for flask/gunicorn or data streaming
# Start gunicorn workers (sudo is required until spectrumbrowser user/group setup complete)
$ sudo make start-workers
# Check the status of workers (may expand this target to give status on more services in future)
$ make status
# Stop gunicorn workers (sudo is required until spectrumbrowser user/group setup complete)
$ sudo make stop-workers
# Currently data streaming must be started completely manually
# (sudo is required until spectrumbrowser user/group setup complete)
$ sudo python flask/DataStreaming &
```

<h2> Location of configuration files </h2>

Take a look at the head of Makefile to see where config files are installed:

```bash
$ head -n 15 Makefile 
# Makefile for SpectrumBrowser

REPO_HOME:=$(shell git rev-parse --show-toplevel)

NGINX_SRC_DIR=${REPO_HOME}/nginx
NGINX_CONF_FILES=nginx.conf cacert.pem privkey.pem mime.types
NGINX_DEST_DIR=$(DESTDIR)/etc/nginx

GUNICORN_SRC_DIR=${REPO_HOME}/flask
GUNICORN_CONF_FILE=gunicorn.conf
GUNICORN_PID_FILE=$(shell python -c "execfile(\"${GUNICORN_SRC_DIR}/${GUNICORN_CONF_FILE}\"); print pidfile")

MSOD_SRC_DIR=${REPO_HOME}
MSOD_CONF_FILE=MSODConfig.json
MSOD_DEST_DIR=$(DESTDIR)/etc/msod
```

So nginx config files will be at:
/etc/nginx/{nginx.conf,cacert.pem,privkey.pem,mime.types}

A file called MSODConfig.json will be installed in `/etc/msod/`. Use MSODConfig.json to modify settings used by flask. Currently available options are:

```bash
$ cat /etc/msod/MSODConfig.json 
{
    "SPECTRUM_BROWSER_HOME": "/opt/SpectrumBrowser",
    "DB_PORT_27017_TCP_ADDR": "localhost",
    "FLASK_LOG_DIR": "/var/log/flask"
}
```

* Location of root repository (should be correctly set by "make install")
* IP address of mongodb host
* Log directory used by flask

Use of this generic config file will likely expand in the future with more options.

Guncicorn config file is read directly from the source repository. Long story short, Debian's gunicorn maintainer has taken a lot of liberties and created a number of incompatibilities between Debian and Redhat. For now, we'll just run gunicorn similar to how it was run before, with the slight added convenience of a config file in `flask/gunicorn.conf` and convenience functions `sudo make start-workers`, `sudo make stop-services`, and `make status` to provide a service-like interface.

<h3> Known Issues </h3>

If you find issues with the Makefile, please submit an issue and assign @djanderson.

Currently known issues:
 - Stopping gunicorn workers should clear memcached cache as per this comment https://github.com/usnistgov/SpectrumBrowser/issues/155#issuecomment-98858509

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

     bitarray: https://pypi.python.org/pypi/bitarray/ pip install bitarray
     PyPubSub: http://pubsub.sourceforge.net/ pip install pypubsub
     SciPy: www.scipy.org (includes numpy, matplotlib - download and install for your OS or individually)
     maplotlib: pip install matplotlib
     numpy: pip install numpy
     Flask: http://flask.pocoo.org/ (pip install flask)
     CORS: extension https://pypi.python.org/pypi/Flask-Cors  (pip install flask-CORS)
     pymongo:  https://pypi.python.org/pypi/pymongo/ (pip install pymongo)
     pypng:  https://github.com/drj11/pypng (pip install pypng)
     pytz:   http://pytz.sourceforge.net/ (pip install pytz)
     pyopenssl: https://github.com/pyca/pyopenssl (pip install pyopenssl)
     gevent: python co-routines  (pip install gevent)
     flask_websockets  (websocket support for flask) : (pip install Flask-Sockets) 
     websockets (python websocket client): https://github.com/liris/websocket-client (pip install websocket-client)
     gunicorn (python wsgi server):  http://gunicorn.org/ 
     sphinx document generation tool: (pip install sphinx)
     sphinx autohttp contrib: (pip install sphinxcontrib-httpdomain)
     python-memcached wrapper for memcache. https://github.com/linsomniac/python-memcached (pip install python-memcache)
     requests HTTP requests package for python  (pip install requests)

     
Install Notes:

If pip install for pubsub does not work (I ran into some problems), do this:

     pip install http://downloads.sf.net/project/pubsub/pubsub/3.3.0/PyPubSub-3.3.0.zip

The --user flag for pip, puts things in  .local under your $HOME.

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

Note that this will build a bootstrap file /var/tmp/MSODConfig.json. This file will be later read by the flask worker process on startup.
If you want to override anything in this bootstrap file, you can do so using a command line parameter to ant. For example, build using
the following command line parameter to change the IP address where mongodb runs:

    ant -Dmongo.host=129.6.55.62

Currently, only one such parameter is defined. If you specify no parameters when you build it, default bootstrap parameters are used 
(i.e. mongo.host) but more will be defined later. 

The default ant target will compile the client side code and generate javascript. Under development, it is only 
set up to optimize code for firefox. To remove this restriction use:

   ant demo 

but it will take longer to compile. Again, override defaults in the bootstrap as above.

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

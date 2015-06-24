
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
# TODO: verify this is true for all users, not just the one who did the original clone

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
# Start service scripts
$ sudo service memcached start # (stop/restart/status, etc)
$ sudo service nginx start # (stop/restart/status, etc)
$ sudo service spectrumbrowser start # (stop/restart/status)
$ sudo service streaming start # (stop/restart/status)
$ sudo service occupany start # (stop/restart/status)
# Monitor log files:
$ tail -f /var/log/gunicorn/*.log -f /var/log/flask/*.log -f /var/log/nginx/*.log -f /var/log/memcached.log -f /var/log/streaming.log -f /var/log/occupancy.log -f /var/log/admin.log
```

<h2> Location of configuration files </h2>

We can take a look at the output of `sudo make install` to see where files are being installed:

```bash
$ sudo make install
install -D -m 644 /opt/SpectrumBrowser/nginx/nginx.conf /etc/nginx/nginx.conf
install -D -m 644 /opt/SpectrumBrowser/nginx/cacert.pem /etc/nginx/cacert.pem
install -D -m 644 /opt/SpectrumBrowser/nginx/privkey.pem /etc/nginx/privkey.pem
install -D -m 644 /opt/SpectrumBrowser/nginx/mime.types /etc/nginx/mime.types
install -m 644 /opt/SpectrumBrowser/flask/gunicorn.conf /etc/gunicorn.conf
install -m 644 /opt/SpectrumBrowser/services/spectrumbrowser-defaults /etc/default/spectrumbrowser
install -m 755 /opt/SpectrumBrowser/services/spectrumbrowser-init /etc/init.d/spectrumbrowser
install -m 755 /opt/SpectrumBrowser/services/streaming-bin /usr/bin/streaming
install -m 755 /opt/SpectrumBrowser/services/streaming-init /etc/init.d/streaming
install -m 755 /opt/SpectrumBrowser/services/occupancy-bin /usr/bin/occupancy
install -m 755 /opt/SpectrumBrowser/services/occupancy-init /etc/init.d/occupancy
install -m 755 /opt/SpectrumBrowser/services/admin-bin /usr/bin/admin
install -m 755 /opt/SpectrumBrowser/services/admin-init /etc/init.d/admin
install -D -m 644 /opt/SpectrumBrowser/MSODConfig.json /etc/msod/MSODConfig.json
install -m 755 /opt/SpectrumBrowser/services/msod-init /etc/init.d/msod
Hardcoding SPECTRUM_BROWSER_HOME as /opt/SpectrumBrowser in /etc/msod/MSODConfig.json
```

*spectrumbrowser*:
 - `/etc/gunicorn/gunicorn.conf` Config file
 - `/etc/init.d/spectrumbrowser` Init script (shouldn't need to modify directly)
 - `/etc/default/spectrumbrowser` Modify to override init script variables

*streaming*
 - `/usr/bin/streaming` Helper script to launch script as a service
 - `/etc/init.d/streaming` Init script (shouldn't need to modify directly)

*occupancy*
 - `/usr/bin/occupancy` Helper script to launch script as a service
 - `/etc/init.d/occupancy` Init script (shouldn't need to modify directly)

*admin*
 - `/usr/bin/admin` Helper script to launch script as a service
 - `/etc/init.d/admin` Init script (shouldn't need to modify directly)
 
*nginx*:
 - `/etc/nginx/{nginx.conf,cacert.pem,privkey.pem,mime.types}`

*Flask*:
 - `/etc/msod/MSODConfig.json` See below

```bash
 $ cat /etc/msod/MSODConfig.json 
{
    "SPECTRUM_BROWSER_HOME": "/opt/SpectrumBrowser",
    "DB_PORT_27017_TCP_ADDR": "localhost",
    "FLASK_LOG_DIR": "/var/log/flask"
}
```

Use MSODConfig.json to modify:
 - Location of root repository (should be correctly set by "make install")
 - IP address of mongodb host
 - Log directory used by flask
 - Location for the database

Use of this generic config file will likely expand in the future with more options.

*streaming*:
 - `/etc/init.d/streaming` Init script (shouldn't need to modify directly)
 - `/etc/default/streaming` If created, will override variables in init script
 - `/usr/bin/streaming` A small helper script to start streaming as a daemon

<h3> Known Issues </h3>

     - None

If you find issues with the Makefile or gunicorn/streaming init script, please submit an issue and assign @djanderson.


<h2> How to build and run it manually </h2>


<h3> Dependencies </h3>

This section is intended for developers.

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

     PyZmQ: https://github.com/zeromq/pyzmq  Python Wrapper for zeromq pubsub library.
     bitarray: https://pypi.python.org/pypi/bitarray/ pip install bitarray
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

     
The --user flag for pip, puts things in  .local under your $HOME.

If you are not using virtualenv for your install, set up your PYTHONPATH environment variable 
according to where your python packages were installed. For example:

     $HOME/.local/lib/python2.6/site-packages/ AND $HOME/.local/usr/lib/python2.6/site-packages/ $HOME/.local/usr/lib64/python2.6/site-packages



<h3> Operating Systems </h3>

This is primarily a linux based project. We will not be testing under
windows.  My development platform is  Linux (Centos 6.5). Streaming
support will only work on a system that supports websockets for wsgi.
This currently only works on Linux.  If you choose to run under Windows,
you cannot run gunicorn and hence your server will consist of a single
flask worker process, resulting in bad performance for multi-user access.

<h3> Build it </h3>

The GWT_HOME environment variable should point to where you have gwt installed.
The SPECTRUM_BROWSER_HOME variable should point to where you have git cloned the installation.

    cd $SPECTRUM_BROWSER_HOME
    ant


The default ant target will compile the client side code and generate javascript. Under development, it is only 
set up to optimize code for firefox. To remove this restriction use:

   ant demo 

but it will take longer to compile. Again, override defaults in the bootstrap as above.

<h3> Run it </h3>


Populate the database (you only have to do this once). 
I will assume you are using a unix shell. Feel free to update the instructions.

Copy this MSODConfig.json file to $HOME/.mosod to modify your own configuration.

Start the mongo database server

    sh start-db.sh 
    (wait till it initializes and announces that it is ready for accepting connections)

Populate the DB with test data (I am using the LTE data as an example for test purposes)
    
    define an environment variable TEST_DATA_HOME
    mkdir $TEST_DATA_HOME
   
Put the following files in $TEST_DATA_HOME

     FS0714_173_7236.dat  
     LTE_UL_DL_bc17_bc13_ts109_p1.dat  
     LTE_UL_DL_bc17_bc13_ts109_p2.dat  
     LTE_UL_DL_bc17_bc13_ts109_p3.dat

    This will run for a while ( about 5 minutes)

    (these files are not on github - too big. Ask mranga@nist.gov for data files when you are ready for this step.)

If you have populated the DB with data that corresponds to a previous version of MSOD (> MSOD-06), then upgrade the data using

    python upgrade-db.py

For debugging, start the development web server (only supports http and only one Flask worker)

    cd $SPECTRUM_BROWSER_HOME/flask
    python flaskr.py

OR for multi-worker support (better throughput)

   bash scripts/start-gunicorn.sh 

Configure the system

    Point your browser at http://localhost:8001/admin
    The default admin user name is admin@nist.gov password is Administrator12!

Restart the system after the first configuration.

Load any static data.

Browse the data

   point your browser at http://localhost:8000/spectrumbrowser

<h3> Stopping the system</h3>

To stop the database

   sh scripts/stop-db.sh

To stop flask

   sh scripts/stop-gunicorn.sh



<h2> LIMITATIONS </h2>

There are several limitations at present. Here are a few :

This project (including this page) is in an early state of development.

BUGS are not an optional feature. They come bundled with the software
at no extra cost.

Testing testing and more testing is needed. Please report bugs and suggestions.
Use the issue tracker on github to report issues.

For HTTPS support, you need to run the production Nginx httpd
web server. See configuration instructions in the httpd directory.

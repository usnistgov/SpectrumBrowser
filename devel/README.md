
<h1> Build Instructions </h1>

<h2> Deploy system locally using install_stack.sh and Makefile </h2>

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
$ sudo ./install_mongod.sh
# Follow instructions to log out and back in if GWT was not previously installed
$ cd -
# Edit the DB_PORT_27017_TCP_ADDR field in /opt/SpectrumBrowser/MSODConfig.json
# The default target runs "ant" and the install target installs and/or modifies 
# config files for nginx, gunicorn, and flask
# cd to the root of the SpectumBrowser repository
$ git pull

$ make && sudo make REPO_HOME=`pwd` install
# To build the "demo" target
$ make demo && sudo make REPO_HOME=`pwd` install
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



<h2> Deployment remotely on remote host (e.g. virtual machine) </h2>

Install fabric:

    pip install -r python_devel_requirements.txt

Set your environment variable:

    export MSOD_WEB_HOST=target_ip_address

You should have no password root access to the remote host with address target_ip_address. 
To do this, use ssh-copy-id to copy your ssh ID to the remote host.
Using the fab deployment tool, we can push our installation to the remote host:

First, pack things up:

    fab pack

And deploy it :

    fab deploy

Note that the build tools are not deployed on the remote host. 
The target deployment host should be running centos 6.6 or RedHat 7.
TODO: Add support for db and Web front end running on different hosts.

<h2>Developer Notes </h2>

This section is intended for developers. It explains the dependencies and what they are used for and also instructs you
on how to start the system using provided shell scripts.

<h3> Detailed description of Dependencies </h3>


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

You can install all the following OS dependencies at once by running yum for the dependencies in redhat_stack.txt
The script install_stack.sh does this. 



Assuming you took my advice and installed virtualenv, now define a 
virtualenv in which you do your python installs so you won't need to be root 
or do local installs for your python packages:

     mkvirtualenv sb
     workon sb

Now proceed to install python depenencies. You can install dependencies all at once by using:

     pip install -r python_pip_requirements.txt --user

     (leave out the --user if you are using virtualenv)

Here is a description of the dependencies, websites for the dependencies, and what they do:

     PyZmQ: https://github.com/zeromq/pyzmq  Python Wrapper for zeromq pubsub library.
     bitarray: https://pypi.python.org/pypi/bitarray/ For the occupancy server
     SciPy: www.scipy.org (includes numpy, matplotlib - download and install for your OS or individually)
        maplotlib: pip install matplotlib
        numpy: For array grinding.
     Flask: http://flask.pocoo.org/ The mother of all web service containers.
     CORS: extension https://pypi.python.org/pypi/Flask-Cors  Multi site support.
     pymongo:  https://pypi.python.org/pypi/pymongo/ Mongo connection wrapper.
     pypng:  https://github.com/drj11/pypng For image processing.
     pytz:   http://pytz.sourceforge.net/ Timezone conversion.
     pyopenssl: https://github.com/pyca/pyopenssl secure socket support.
     gevent: python co-routines  for websockets.
     flask_websockets  websocket support for flask
     websockets  https://github.com/liris/websocket-client (pip install websocket-client)
     gunicorn http://gunicorn.org/ (python load balancing server):  
     sphinx: document generation tool
     sphinx autohttp contrib: (pip install sphinxcontrib-httpdomain)
     python-memcached wrapper for memcache. https://github.com/linsomniac/python-memcached (pip install python-memcache)
     requests HTTP requests package for python  

Note that the --user flag for pip, puts things in  .local under your $HOME.

If you are <b>not</b> using virtualenv for your install, set up your PYTHONPATH environment variable 
according to where your python packages were installed. For example:

     $HOME/.local/lib/python2.6/site-packages/ AND $HOME/.local/usr/lib/python2.6/site-packages/ $HOME/.local/usr/lib64/python2.6/site-packages



<h3> Build it </h3>

The GWT_HOME environment variable should point to where you have gwt installed.
The SPECTRUM_BROWSER_HOME variable should point to where you have git cloned the installation.

    cd $SPECTRUM_BROWSER_HOME
    ant


The default ant target will compile the client side code and generate javascript. Under development, it is only 
set up to optimize code for firefox. To remove this restriction use:

   ant demo 

but it will take longer to compile. Again, override defaults in the bootstrap as above.

Please look at readme.md in the unit-tests directory on how to test the system.


<h2> LIMITATIONS </h2>

This is a linux project. There are no plans to port this to windows.

There are several limitations at present. Here are a few :

This project (including this page) is in an early state of development.

BUGS are not an optional feature. They come bundled with the software
at no extra cost.

Testing testing and more testing is needed. Please report bugs and suggestions.
Use the issue tracker on github to report issues.


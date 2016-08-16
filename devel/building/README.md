
<h3> Building the system </h3>


Install dependencies as outlined in ../requirements/README.md

The GWT\_HOME environment variable should point to where you have gwt installed.
The SPECTRUM\_BROWSER\_HOME variable should point to where you have git cloned the installation.

    cd $SPECTRUM_BROWSER_HOME
    ant


The default ant target will compile the client side code and generate javascript. Under development, it is only 
set up to optimize code for firefox. To remove this restriction use:

   ant demo 

but it will take longer to compile. Again, override defaults in the bootstrap as above.

NOTE: Automated install fab scripts are located at ../deploy. Please use those to install the system
on a virtual machine. 

<h3>Developer Tips</h3>

This section is intended for developers. It explains the dependencies and what they are used for and also instructs you
on how to start the system using provided shell scripts.

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
You can install all the following OS dependencies at once by running yum for the dependencies in redhat\_stack.txt
The script install\_stack.sh does this. 



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

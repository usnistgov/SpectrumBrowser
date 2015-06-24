# To get ready for testing:
# 1. On the mongodB Dev VM:
# install mongoDb version 2.6.3 (we need this versio) on the RedHat mongo server. Note: this is what I did on Ubuntu:
sudo apt-get install -y mongodb-org=2.6.3 mongodb-org-server=2.6.3 mongodb-org-shell=2.6.3 mongodb-org-mongos=2.6.3 mongodb-org-tools=2.6.3
# In /etc/init/mongod.conf -> set ENABLE_MONGOD=yes
# start the mongod service, if not already started from installation
mongod -dbpath path/to/data/db

# 2.1 On the Spectrum Browser Server Dev VM:
# Install the software stack & python pip software by running the following:
sudo devel/install_stack.sh

# 2.2 load the test data:
python Config.py -f unit-tests/Config.bldr.txt init
python AccountsManagement -f unit-tests/Accounts.bldr.txt init
python SensorDb.py -f unit-tests/Sensors.bldr.txt init
# The following will take a long time, e.g. 5-10 minutes:
# Note: make sure to go to the mongodb VM and in data/db enter:
rm spectrumdb.*
# On the Spectrum Browser server VM, run the following:
python populate_db.py -data ../../DataSpectrumBrowser/FS0714_173_5275.dat
python populate_db.py -data ../../DataSpectrumBrowser/LTE_UL_DL_bc17_bc13_ts109_p1.dat
python populate_db.py -data ../../DataSpectrumBrowser/LTE_UL_DL_bc17_bc13_ts109_p2.dat
python populate_db.py -data ../../DataSpectrumBrowser/LTE_UL_DL_bc17_bc13_ts109_p3.dat

# 2.3 Run the services make file
sudo make install

# 2.4 start the services, e.g.
sudo service memcached start
sudo service gunicorn start
# question: what is the streaming service called?
sudo service nginx start

#Note: to stop any services do the above commands with "stop" instead of "start"
# e.g. sudo service memcached stop

#Note: to uninstall the services make file:
# sudo make uninstall

# 2.5 Until make file is working, to manually start processes:
sudo /etc/init.d/memcached restart
cd $SPECTRUM_BROWSER_HOME/flask
# make sure you have downloaded the latest spectrum browser code from git and compile the code:
ant demo
gunicorn -w 1 -k flask_sockets.worker flaskr:app  -b '0.0.0.0:8000' --debug --log-file - --error-logfile -
python DataStreaming.py&
sudo /usr/sbin/nginx -c $SPECTRUM_BROWSER_HOME/nginx/nginx.conf
# pass phrase is ranga

# 2.6 To test streaming run the following:
cd $SPECTRUM_BROWSER_HOME
python unit-tests/test-streaming-socket.py -data ../../../DataSpectrumBrowser/LTE_UL_bc17_ts109_stream_30m.dat



<h2>Deployment on remote host</h2>

This directory contains fabric scripts to automate deployment on remote hosts. You are expected to have a 
sudo account on the host where you want to deploy.

<ul>

<li>Define two environment variables : 

    MSOD_WEB_HOST  is the  host where you want the web services to live.
    MSOD_DB_HOST is the host where you want the database to live.

    export MSOD_WEB_HOST=target_ip_address
    export MSOD_DB_HOST=target_db_host_address

These two variables can be the same if DB and web pieces are co-resident.

<li>Install Prerequisites
    
    See instructions in the ../requirements/README.md file.

<li>Install Fabric

    pip install ../requirements/python_devel_requirements.txt

<li>Build it locally

    follow instructions in the ../building/README.md file.

<li>Pack it 

    fab  pack

<h3>Deploy</h3>

Deploy Server to MSOD_WEB_HOST target and deploy db to MSOD_DEB_HOST target:

    fab -u ec2-user -i /home/mranga/.ssh/CTL-MSOD2.pem deploy

Here I assume user ec2-user has a sudo account with ssh setup with no password on buildServer.
The identity file for password-less login is /home/mranga/.ssh/CTL-MSOD2.pem
Use ssh-kegen and ssh-copy-id go generate and push ssh keys.
Note that the build tools are not deployed on the remote host. 
The target deployment host should be running centos 6.6 or RedHat 7.

Please look at README.md in the unit-tests directory on how to test the system.


<h2> Run Services </h2>

```bash
# Start service scripts
$ sudo service memcached start # (stop/restart/status, etc)
$ sudo service nginx start # (stop/restart/status, etc)
$ sudo service spectrumbrowser start # (stop/restart/status)
$ sudo service admin start # (stop/restart/status)
$ sudo service occupany start # (stop/restart/status)
$ sudo service streaming start # (stop/restart/status)
$ sudo service monitoring start # (stop/restart/status)
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






NIST USRP Spectrum Sensor
=========================

Quick Start
-----------

1. Build and install gr-myblocks in your GNU Radio installation.
        $ cd gr-myblocks
        $ mkdir build
        $ cd build
        $ cmake [optional switches] ../
        $ make && make test
        $ sudo make install

2. Install the python modules 'json' and 'requests'.  The latter is needed
   only by spectrum_monitor_post.py.

3. Edit the sensor.loc file with your sensor's latitude/longitude
   coordinates (decimal), altitude (m), and time zone (string).

4. Edit the sensor.sys file with your sensor's specifications.

5. Run the python script spectrum_monitor_file.py (writes acquisitions to a
   file) or spectrum_monitor_post.py (posts acquisitions to a url) with the
   '--help' option to see command line options.  Files sensor.loc and
   sensor.sys must be in the local directory.

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

Now simply start the server and attach the sensor to it.
```bash
docker run -d --name mongodb_data -v /data/db busybox
docker run -d --volumes-from mongodb_data --name mongodb ntiaits/mongodb
docker run -d -p 8000:8000 --name sbserver --link mongodb:db ntiaits/spectrumbrowser-server
TODO: Add instructions for interfacing with spectrumbrowser-server image here! The sensor
docker run -d --name sbsensor ((link of port forward to sbserver)) ntiaits/spectrumbrowser-sensor
```

Some other things to try:
```bash
docker restart sbsensor
# (For debugging--this will start an interactive term in the container)
docker run -tiP --rm ntiaits/spectrumbrowser-sensor /sbin/my_init -- /bin/bash -l
```

And finally, if you make changes to code affecting the server, feel free to rebuild the image and push it out!
```bash
cd $SPECTRUM_BROWSER_HOME/USRPSpectrumSensor
docker build -t ntiaits/spectrumbrowser-sensor .
docker push ntiaits/spectrumbrowser-sensor
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


Notes
-----
* Tested with GNU Radio 3.7.2.1 and Python 2.6 and 2.7.
* Complies with version 1.0.9 of the NTIA/NIST Measured Spectrum Occupancy
  Database data transfer specification.

Technical Support
-----------------
Michael Souryal
National Insitute of Standards and Technology
souryal@nist.gov

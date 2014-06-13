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

Notes
-----
* Tested with GNU Radio 3.7.2.1 and Python 2.6 and 2.7.
* Complies with version 1.0.6 of the NTIA/NIST Measured Spectrum Occupancy
  Database data transfer specification.

Technical Support
-----------------
Michael Souryal
National Insitute of Standards and Technology
souryal@nist.gov


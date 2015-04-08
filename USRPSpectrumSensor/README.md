NIST USRP Spectrum Sensor
=========================

Quick Start
-----------

1. Build and install gr-myblocks in your GNU Radio installation.

    $ cd gr-myblocks
    $ mkdir build
    $ cd build
    $ cmake [optional switches] ../
      (e.g., cmake -DCMAKE_INSTALL_PREFIX=<install_dir> ../)
    $ make && make test
    $ sudo make install

2. Install any missing python modules (e.g., json, requests).

3. Edit the sensor.loc file with your sensor's latitude/longitude
   coordinates (decimal), altitude (m), and time zone (string).

4. Edit the sensor.sys file with your sensor's specifications.

5. Run the python script spectrum_monitor_file.py (writes stream to a
   file), spectrum_monitor_post.py (posts acquisitions to an https server),
   or spectrum_monitor_sslsocket.py (writes stream to an ssl socket) with
   the '--help' option to see command line options.  Files sensor.loc and
   sensor.sys must be in the local directory.  Shell script run_sensor.sh
   gives an example for invoking spectrum_monitor_file.py.

Notes
-----

    * Tested with GNU Radio 3.7.2.1 and Python 2.6 and 2.7.
    * Complies with version 1.0.12 of the NTIA/NIST Measured Spectrum Occupancy
      Database data transfer specification.

Technical Support
-----------------

   Michael Souryal
   National Insitute of Standards and Technology
   souryal@nist.gov


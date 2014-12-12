USRP Analyzer
=============

USRP Analyzer provides a spectrum analyzer-like graphical interface to
the USRP. It is build on
[GNURadio](http://gnuradio.org/redmine/projects/gnuradio/wiki) and
[SciPy](http://www.scipy.org/).

![USRP Analyzer screenshot](extras/usrp_analyzer_scrnshot.png)

Key Features
------------

* Spectrum sweep capability
* Marker with global peak search
* Peak search in selected region (demo'd in screenshot)
* Output to log if user-selected threshold is exceeded (demo'd in screenshot)
* Export raw and post-FFT I/Q data to Matlab file
* Custom blocks to:
  * linear average multiple passes
  * drop N samples from the stream after frontend retune
* Easily decouple GUI from processing code

Quick Start
-----------
1. Install GNURadio and UHD (recommend using [PyBombs](https://github.com/pybombs/pybombs))
2. Don't forget to `./pybombs env` and then `source setup_env.sh`
3. Install Python dependencies: `python-wxgtk2.8, python-scipy` (List may be incomplete)
4. Build and install custom blocks:
```bash
$ cd USRPAnalyzer/blocks/gr-usrpanalyzer
$ mkdir build && cd build
$ cmake -DCMAKE_INSTALL_PREFIX:PATH=~/YOUR_PYBOMBS_TARGET ../ && make all install
```

To run, try something like `$ ./usrp_analyzer.py 650M 750M --dwell=30 --tune-delay=1024 --continuous`

Todo
----
 - [ ] Support dwelling on a frequency for a time interval (requested by Jeff)

Support
-------
Douglas Anderson | NTIA/Institute for Telecommunication Sciences | danderson@bldrdoc.its.gov

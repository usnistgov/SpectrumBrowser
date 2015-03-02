# spectrummonitoring Dockerfile for the NIST/ITS Spectrum Monitoring Project


# Phusion is an Ubuntu image optimized for Docker
FROM phusion/baseimage:0.9.16

# spectrummonitoring Dockerfile maintainer:
MAINTAINER Douglas Anderson danderson@its.bldrdoc.gov

# Use baseimage-docker's init system.
CMD ["/sbin/my_init"]

RUN apt-get update && apt-get -y install git-core cmake g++ \
    python-dev swig pkg-config libfftw3-dev libboost-all-dev libcppunit-dev \
    libgsl0-dev libusb-dev libsdl1.2-dev python-wxgtk2.8 python-numpy \
    python-cheetah python-lxml doxygen libxi-dev python-sip \
    libqt4-opengl-dev libqwt-dev libfontconfig1-dev libxrender-dev \
    python-sip python-sip-dev python-requests

RUN mkdir -p /home/spectrum/{pybombs,USRPSpectrumSensor}

RUN git clone https://github.com/pybombs/pybombs.git /home/spectrum/pybombs
WORKDIR /home/spectrum/pybombs
COPY docker/pybombs.conf config.dat
RUN ./pybombs install uhd gnuradio

# Set ENV vars the "Phusion" way
RUN echo "/usr/local/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/lib64/qt4/bin/" > /etc/container_environment/PATH
RUN echo "/usr/local/python/:/usr/local/lib/python2.6/site-packages/:/usr/local/lib64/python2.6/site-packages/:/usr/local/lib/python2.6/dist-packages/:/usr/local/lib64/python2.6/dist-packages/:/usr/local/lib/python2.7/site-packages/:/usr/local/lib64/python2.7/site-packages/:/usr/local/lib/python2.7/dist-packages/:/usr/local/lib64/python2.7/dist-packages/:/usr/local/python/:/usr/local/lib/python2.6/site-packages/:/usr/local/lib64/python2.6/site-packages/:/usr/local/lib/python2.6/dist-packages/:/usr/local/lib64/python2.6/dist-packages/:/usr/local/lib/python2.7/site-packages/:/usr/local/lib64/python2.7/site-packages/:/usr/local/lib/python2.7/dist-packages/:/usr/local/lib64/python2.7/dist-packages/" > /etc/container_environment/PYTHONPATH
RUN echo "/usr/local/lib/:/usr/local/lib64/:" > /etc/container_environment/LD_LIBRARY_PATH
RUN echo "/usr/local/lib/pkgconfig/:/usr/local/lib64/pkgconfig/:" > /etc/container_environment/PKG_CONFIG_PATH

# Copy over Git repo
COPY . /home/spectrum/USRPSpectrumSensor

WORKDIR /home/spectrum/USRPSpectrumSensor

# Build blocks
RUN mkdir -p gr-myblocks/build && \
    cd gr-myblocks/build && \
    cmake ../ && \
    make && \
    make install

COPY spectrum_monitor_post.py /usr/bin/spectrum_monitor_post
RUN mkdir /etc/service/spectrum_monitor
COPY docker/spectrum_monitor_post.sh /etc/service/spectrum_monitor/run
RUN chmod +x /usr/bin/spectrum_monitor_post /etc/service/spectrum_monitor/run

# Clean up APT and temp dir when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /home/spectrum/pybombs

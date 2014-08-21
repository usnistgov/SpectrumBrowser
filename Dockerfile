# spectrummonitoring Dockerfile for the NIST/ITS Spectrum Monitoring Project


# Pull in the latest official Ubuntu image
FROM ubuntu:latest

# spectrummonitoring Dockerfile maintainer:
MAINTAINER Douglas Anderson danderson@its.bldrdoc.gov


# Update Ubuntu non-interactively
RUN apt-get update -y

# Install SpectrumBrowser dependencies
RUN apt-get install -y python-dev python-scipy python-matplotlib python-pip \
  python-simplejson python-flask python-pymongo python-tz python-openssl \
  python-gevent python-websocket swig libagg-dev wget unzip default-jdk ant

# Download and Install the GWT SDK
RUN wget -P /tmp http://storage.googleapis.com/gwt-releases/gwt-2.6.1.zip && \
  unzip /tmp/gwt-2.6.1 -d /opt

# Set environment variables that will persist for the rest of the build, as well as
# when the resulting image is run
ENV GWT_HOME /opt/gwt-2.6.1

# Copy our git repo into our image, set its location in the environment, and cd to it
ADD . /home/spectrum/SpectrumBrowser
ENV SPECTRUM_BROWSER_HOME /home/spectrum/SpectrumBrowser
WORKDIR /home/spectrum/SpectrumBrowser

# Built the project
RUN ant

# Create supervisor's log directory
RUN mkdir -p /var/log/supervisor

# FIXME: Julie said she got all deps through apt? Can't find pypng or Flask-Sockets
# It also appears we need pymongo >= 2.7 for .initialize_ordered_bulk_op(), which
# isn't in ubuntu repos
RUN pip install --upgrade pypng pymongo Flask-Sockets

# Open port 8000 (used by Flask)
EXPOSE 8000

# FIXME: cd to /home/spectrum/SpectrumBrowser/flask because flaskr.py fails otherwise
WORKDIR /home/spectrum/SpectrumBrowser/flask

CMD ["python", "flaskr.py"]

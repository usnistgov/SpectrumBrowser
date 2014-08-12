# spectrummonitoring Dockerfile for the NIST/ITS Spectrum Monitoring Project


# Pull in the latest official CentOS image
FROM centos:latest

# spectrummonitoring Dockerfile maintainer:
MAINTAINER Douglas Anderson danderson@its.bldrdoc.gov

# Add mongodb repo to the image
ADD docker/mongo.repo /etc/yum.repos.d/mongodb.repo

# Update CentOS non-interactively
RUN yum update -y

# Install non-Python SpectrumBrowser dependencies that are in the CentOS repo
RUN yum groupinstall --setopt=group_package_types=mandatory -y 'Development Tools'

RUN yum install -y mongodb-org openssl-devel python-devel libffi-devel lapack-devel blas-devel \
    libpng-devel freetype-devel ant agg wget git

# get pip, a tool for installing and managing Python packages
RUN wget -P /tmp https://bootstrap.pypa.io/get-pip.py && python /tmp/get-pip.py

# Install SpectrumBrowser dependencies that are in PyPI - the Python Package Index
RUN pip install --upgrade six numpy pymongo pypng pytz pyopenssl matplotlib \
  gevent Flask-Sockets websocket-client freetype-py pyparsing scipy supervisor

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

# We will load MongoDB's database directory as a persistant data container
VOLUME ["/data/db"]

# Create supervisor's log directory
RUN mkdir -p /var/log/supervisor

# Copy the file which runs and monitors our server processes
COPY docker/startserver.sh /usr/local/bin/startserver.sh
RUN chmod u+x /usr/local/bin/startserver.sh

# Open port 8000 (used by Flask)
EXPOSE 8000

# FIXME: cd to /home/spectrum/SpectrumBrowser/flask because flaskr.py fails otherwise
WORKDIR /home/spectrum/SpectrumBrowser/flask

CMD ["/usr/local/bin/startserver.sh"]

# Mongodb Dockerfile for the NIST/ITS Spectrum Monitoring Project


# Pull in the latest official Ubuntu image
FROM ubuntu:latest

# spectrummonitoring Dockerfile maintainer:
MAINTAINER Douglas Anderson danderson@its.bldrdoc.gov

# Add MongoDB's key to apt
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10

RUN echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' | \
  sudo tee /etc/apt/sources.list.d/mongodb.list

# Update Ubuntu non-interactively
RUN apt-get update -y

# Install MongoDB and tools
RUN apt-get install -y mongodb-org

# Create out database directory
RUN mkdir -p /data/db

# Let Docker know that we'll be mounting the database storage at runtime
VOLUME ["/data/db"]

WORKDIR /data

# Expose ports
#   - 27017: process
#   - 28017: http
EXPOSE 27017
EXPOSE 28017

CMD ["mongod"]

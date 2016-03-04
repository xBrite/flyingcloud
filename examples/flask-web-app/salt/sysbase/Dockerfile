# FlyingCloud base image - phusion/baseimage + SaltStack
# Note: never use :latest, always use a numbered release tag.
FROM phusion/baseimage:0.9.18
MAINTAINER MetaBrite, Inc.

# Use baseimage-docker's init system.
CMD ["/sbin/my_init"]

# After the image is built, we will use salt, mounted via docker run.

# Update the sources list
RUN apt-get update

# Install salt and basic applications
RUN apt-get install -y tar git vim nano wget net-tools build-essential salt-minion

# SaltStack fail hard if any state fails
RUN echo "failhard: True" >> /etc/salt/minion

# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

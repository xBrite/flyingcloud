.. FlyingCloud documentation master file, created by
   sphinx-quickstart on Fri Feb 26 22:02:50 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


FlyingCloud: complex Docker images made simple
----------------------------------------------

FlyingCloud makes generating Docker_ images fast and easy by using SaltStack_.

**Configure your images - don't use scripts**

* Use `Salt states`_ to configure images instead of using Dockerfiles - Salt already
  can do most system administration without writing code. Salt states are simply YAML_
  files.

**Build Docker images in Continuous Integration**

* FlyingCloud makes it easy to set up multi-stage CI builds of different Docker image layers.

**Run tests inside your Docker images**

* Test the actual artifact that you are deploying - run your tests inside your Docker images.

** Documentation

 - :ref:`Installing <installing>`
 - :ref:`Quickstart <quickstart>`
 - :ref:`Usage <usage>`




Contents
--------

.. toctree::
   :maxdepth: 2



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _Docker: 
    http://docker.com
.. _SaltStack:
    http://saltstack.com/
.. _`Salt states`:
    https://docs.saltstack.com/en/latest/topics/tutorials/starting_states.html
.. _YAML:
    https://en.wikipedia.org/wiki/YAML


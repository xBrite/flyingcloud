***********
flyingcloud
***********

===================================
Build Docker images using SaltStack
===================================

This is a Python library and set of tools that lets you build `Docker <http://docker.com>`_ images using 
masterless `SaltStack <http://saltstack.com/>`_ instead of (or in addition to) using Dockerfiles.

============================
Why would I want to do that?
============================

* Because you are installing a complex stack of software and have outgrown Docker's simple installation system.
* Because you want to install the same software stack on developer workstations and don't want to
  maintain two separate ways of installing a complex stack of software.

============
Installation
============

.. code-block:: bash

    $ pip install flyingcloud

============
Contributing
============


We welcome contributions. This project is in an early stage and under heavy development. 
To contribute, submit a pull request, or contact the developers directly:

* Adam Feuer <adam@metabrite.com>
* George Reilly <george@metabrite.com>

=======
License
=======

* `Apache License v2.0 <http://www.apache.org/licenses/LICENSE-2.0>`_

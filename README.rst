***********
flyingcloud
***********

===================================
Build Docker images using SaltStack
===================================

This is a Python library and set of tools that lets you build `Docker <http://docker.com>`_ images using 
`SaltStack <http://saltstack.com/>`_ instead of (or in addition to) using Dockerfiles.

============================
Why would I want to do that?
============================

* Because you are installing a complex stack of software and have outgrown Docker's simple installation system.
* Because you want to configure your Docker layers instead of writing shell scripts.
* Because you want to install the same software stack on developer workstations and don't want to
  maintain two separate ways of installing a complex stack of software.

============
How it works
============

FlyingCloud runs `Salt <https://docs.saltstack.com/en/latest/>`_
in `masterless mode <https://docs.saltstack.com/en/latest/topics/tutorials/quickstart.html>`_,
applying `Salt states <https://docs.saltstack.com/en/latest/topics/tutorials/starting_states.html>`_
for each Docker layer. Layers can also run custom Python code if necessary.

Salt states can do many system administration tasks solely with configuration.
`Here's a list of all the built-in Salt states <https://docs.saltstack.com/en/develop/ref/states/all/index.html>`_.
`And you can write your own <https://docs.saltstack.com/en/latest/ref/states/writing.html>`_.

============
Installation
============

.. code-block:: bash

    $ pip install flyingcloud

============
Contributing
============


We welcome contributions. This project is in an early stage and under heavy development. 
To contribute, join the Google Group or file a pull request.

* `FlyingCloud Google Group <https://groups.google.com/forum/#!forum/flyingcloud-users>`_

=======
License
=======

* `Apache License v2.0 <http://www.apache.org/licenses/LICENSE-2.0>`_

==============================================
FlyingCloud: Complex Docker Images Made Simple
==============================================

FlyingCloud makes generating Docker_ images fast and easy by using SaltStack_.

.. image:: FlyingCloud_logo.jpg


Advantages
==========

**Configure your images — don't use scripts**

* Use `Salt states`_ to configure images instead of using Dockerfiles —
  Salt already can do most system administration without writing code.
  Salt states are simply YAML_ files.

**Build Docker images in Continuous Integration**

* FlyingCloud makes it easy to set up multi-stage CI builds of different Docker image layers.

**Run tests *inside* your Docker images**

* Test the actual artifact that you are deploying — run your tests inside your Docker images.


Documentation
-------------

 - :ref:`Installing <installing>`
 - :ref:`Configuration <configuration>`
 - :ref:`Usage <usage>`


Example
-------

The `Flask Web App Example`_ shows how to create several reusable Docker images,
built on each other,
along with a small web application
and an example of running tests inside the Docker container.


Presentations
-------------

* `PuPPy, March 2016`_


Contributing
------------

We welcome contributions. This project is in an early stage and under heavy development.
To contribute, join the Google Group or file a pull request.

* `GitHub FlyingCloud Repository`_
* `FlyingCloud Google Group`_
* `FlyingCloud at PyPI`_


License
-------

* `Apache License v2.0`_


Contents
--------

.. toctree::
    :maxdepth: 2


About the FlyingCloud Name
--------------------------

Our name was inspired by the `Flying Cloud clipper ship`_,
which set a record for sailing from New York to San Francisco
that lasted for more than a century.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _Docker: 
    http://docker.com
.. _SaltStack:
    http://saltstack.com/
.. _Salt states:
    https://docs.saltstack.com/en/latest/topics/tutorials/starting_states.html
.. _YAML:
    https://en.wikipedia.org/wiki/YAML
.. _Apache License v2.0:
    http://www.apache.org/licenses/LICENSE-2.0
.. _Flask Web App Example:
    https://github.com/cookbrite/flyingcloud/tree/master/examples/flask-web-app
.. _PuPPy, March 2016:
    https://youtu.be/MbBzuI3p5xw?t=25m23s
.. _GitHub FlyingCloud Repository:
    https://github.com/cookbrite/flyingcloud/
.. _FlyingCloud Google Group:
    https://groups.google.com/group/flyingcloud-users
.. _FlyingCloud at PyPI:
    https://pypi.python.org/pypi/flyingcloud/
.. _Flying Cloud clipper ship:
    https://en.wikipedia.org/wiki/Flying_Cloud_(clipper)

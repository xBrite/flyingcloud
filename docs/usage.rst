
.. _usage:

Usage and Invocations
==========================================


.. _cmdline:

Invoking FlyingCloud
-----------------------------------------------------

FlyingCloud needs to be invoked using command line script ``flyingcloud [...]``
because it uses sudo in some cases (to access the ``docker`` command on linux
or using ``docker-squash`` to squash docker images.

Getting help
------------

::

    flyingcloud -h     # show help on command line and config file options
    flyingcloud --help


Here's what the help will display if you have changed directories to
``examples/flask-web-app``:

::

    usage: main.py [-h] [--timeout TIMEOUT] [--no-pull] [--no-push] [--no-squash]
               [--retries RETRIES] [--debug]
               [--docker-machine-name DOCKER_MACHINE_NAME]
               [--build | --run | --kill]
               {testrunner,app,opencv,pybase,sysbase} ...

    Sample Flask App for FlyingCloud

    optional arguments:
      -h, --help            show this help message and exit
      --timeout TIMEOUT, -t TIMEOUT
                            Docker client timeout in seconds. Default: 300
      --no-pull, -p         Do not pull Docker image from repository
      --no-push, -P         Do not push Docker image to repository
      --no-squash, -S       Do not squash Docker image
      --retries RETRIES, -R RETRIES
                            How often to retry remote Docker operations, such as
                            push/pull. Default: 3
      --debug, -D           Set terminal logging level to DEBUG, etc
      --docker-machine-name DOCKER_MACHINE_NAME, -M DOCKER_MACHINE_NAME
                            Name of machine to use with docker-machine. Default:
                            'default'

    Operations:
      --build, -b           Build a layer. (Default)
      --run, -r             Run a layer.
      --kill, -k            Kill a running layer.

    Layer Names:
      The layers which can be built, run, or killed.

      {testrunner,app,opencv,pybase,sysbase}
        testrunner          Test Runner Layer
        app                 Flask Example App Layer
        opencv              OpenCV Layer
        pybase              Python 2.7.x Layer
        sysbase             Operating System Base Layer


Typical invocations
-------------------

These are some sample command invocations for the example app. For your own app, you would
specify the layer names of your own layers.

::

    flyingcloud --build sysbase
    flyingcloud --build pybase
    flyingcloud --build opencv
    flyingcloud --build app
    flyingcloud --run testrunner

The layers need to be built in order, starting with the bottom layer. Currently you can only specify
one layer per command invocation.

::

    flyingcloud --no-push ...
    flyingcloud --no-pull ...

Do not push or pull the layer no matter what the layer configuration files say.
Sometimes helpful to save time when developing.

::

    flyingcloud --no-squash ...

Do not use `docker-squash <https://github.com/jwilder/docker-squash>`_ to squash the layers,
no matter what the layer configuration files say. Sometimes helpful to save time when developing.

::

    flyingcloud --docker-machine-name ...

On Mac OS X, specify the name of the virtual machine to use when running docker. Ignored on Linux.

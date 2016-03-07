# Flask web app example

This example builds a set of Docker image layers that shows how
to set up a simple Python web app using flask as a web server,
running under uwsgi, fronted by an nginx reverse proxy.

The FlyingCloud configuration files configure the layers.

The flask app uses OpenCV to display an image run through the Canny
edge-detection filter. This example shows how to build Docker layers
that have some complex C-libraries and workarounds that would
normally be scripted in bash.

There is a testrunner layer that can run tests inside the Docker
container to show that you can test the exact artifact in the exact
environment that will be deployed to production.

<img src="https://raw.githubusercontent.com/cookbrite/flyingcloud/feature/documentation-improvements-1/examples/flask-web-app/flask_example_app_layers.png" width="250x" alt="Flask Example App Layers">

## Installing

* `pip install flyingcloud`
* `cd examples/flask-web-app`
* `flyingcloud.sh -h` to see the help and what layers you can build
* `flyingcloud.sh sysbase` to build the OS base layer with SaltStack
* `flyingcloud.sh pybase` to build the Python layer with modern Python 2.7.11 and a virtualenv in `/venv`
* `flyingcloud.sh opencv` to build the layer with OpenCV libraries.
* `flyingcloud.sh app` to build the flask app layer. This is the layer that you will deploy.
* `flyingcloud.sh testrunner` to run tests inside the flask app layer.

## Tips

* To see what the build is doing, `tail -f build_docker.log`
* On a Mac, using the Docker Toolkit, you may have to do this to 
  access the flask app after you run the Docker image:
  * `docker-machine ssh default -f -N -L localhost:8080:localhost:8080`:w
  
  
## Running the Flask App Locally

* `cd examples/flask-web-app/salt/app/application/flask_example_app`
* `pip install -r requirements.txt`
* `./app.py`

## Running Tests Locally

* `pytest tests`
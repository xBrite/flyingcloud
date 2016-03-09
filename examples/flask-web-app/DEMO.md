# Flask Web App Demo

# Preparation
* Before the demo:
    * clean out all Docker containers and images, except Phusion
    * Rebuild: `flyingcloud sysbase; flyingcloud pybase; flyingcloud opencv; flyingcloud app`


# Demo steps

* Demo the web app
    * `flyingcloud --run app`
* use web browser to go to http://localhost:8080
* Run tests with `flyingcloud --run testrunner`
    * `unit` (default)
    * use `-T acceptance`
    * use `-T acceptance -B http://www.google.com` to demonstrate test failure
* Show the app layers picture in README.md
* Demonstrate the options:
    * `flyingcloud --help`
* Explore sample code:
    * `flyingcloud.yaml`
    * all the layers, `layer.yaml`, Salt states, Dockerfiles



* Kill the example JSON API
* try using a different docker machine for puppy demo
* Remove extraneous foundation files

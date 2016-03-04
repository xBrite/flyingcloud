# Flask Web App Demo

* Before the demo:
    * clean out all Docker containers and images, except Phusion
    * Rebuild: `flyingcloud.sh sysbase; flyingcloud.sh pybase; flyingcloud.sh opencv; flyingcloud.sh app`
* Show the app layers slide
* Demonstrate the options:
    * `flyingcloud.sh --help`
* Explore sample code:
    * `flyingcloud.yaml`
    * all the layers, `layer.yaml`, Salt states, Dockerfiles
* Demo the web app
    * `run-worker.sh app`
* use web browser to go to http://localhost:8080
* Run tests with `flyingcloud.sh testrunner`
    * `unit` (default)
    * use `-T acceptance`
    * use `-T acceptance -B http://www.google.com`

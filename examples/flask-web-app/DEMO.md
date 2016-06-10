# Flask Web App Demo

# Preparation
* Before the demo:
  * clean out all Docker containers and images, except Phusion
  * Rebuild:
```bash
  flyingcloud --no-push --no-pull sysbase
  flyingcloud --no-push --no-pull pybase
  flyingcloud --no-push --no-pull opencv
  flyingcloud --no-push --no-pull opencv
  flyingcloud --no-push --no-pull app
```
  * If using the Docker Mac beta:
```bash
    flyingcloud --no-use-docker-machine --no-push --no-pull sysbase
    flyingcloud --no-use-docker-machine --no-push --no-pull pybase
    flyingcloud --no-use-docker-machine --no-push --no-pull opencv
    flyingcloud --no-use-docker-machine --no-push --no-pull opencv
    flyingcloud --no-use-docker-machine --no-push --no-pull app
```

# Demo steps

* Demo the web app (you will need to add `--no-use-docker-machine` if you are using the Docker Mac beta.)
    * `flyingcloud --run app`
* use web browser to go to http://localhost:8080 or http://0.0.0.0:8080
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

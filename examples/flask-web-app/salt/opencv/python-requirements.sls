# "Install" OpenCV into the virtualenv (it can't be installed with pip)
os.packages:
  pkg.installed:
    - fromrepo: trusty
    - pkgs:
      {% if grains['os'] == 'Ubuntu' %}
      - python-opencv
      {% elif grains['os'] == 'MacOS' %}
      - homebrew/science/opencv
      {% endif %}


python-software-properties:
  pkg.installed:
    - fromrepo: trusty
    - pkgs:
      - python-software-properties

# https://launchpad.net/~fkrull/+archive/ubuntu/deadsnakes-python2.7
python2.7-ppa:
  pkgrepo.managed:
    - humanname: Python 2.7 updates PPA
    - name: deb http://ppa.launchpad.net/fkrull/deadsnakes-python2.7/ubuntu trusty main
    - dist: trusty
    - file: /etc/apt/sources.list.d/python27-updates.list
    - keyid: FF3997E83CD969B409FB24BC5BB92C09DB82666C
    - keyserver: keyserver.ubuntu.com
    - require_in: python2.7-update

python2.7-update:
  pkg.latest:
    - fromrepo: trusty
    - pkgs:
      - python2.7
      - python2.7-dev

# needed to get the latest pip
python-pip-bootstrap:
  cmd.run:
    - name: curl https://bootstrap.pypa.io/get-pip.py | python
    - reload_modules: true

python-virtualenv:
  pip.installed:
    - name: 'virtualenv'
    - use_wheel: true

app_venv:
  virtualenv.managed:
    - name: /venv


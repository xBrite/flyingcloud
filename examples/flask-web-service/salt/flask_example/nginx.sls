python-software-properties:
  pkg.installed:
    - fromrepo: trusty
    - pkgs:
      - python-software-properties

# https://chrislea.com/2014/03/20/using-proxy-protocol-nginx/
nginx-devel-ppa:
  pkgrepo.managed:
    - humanname: Python 2.7 updates PPA
    - name: deb http://ppa.launchpad.net/chris-lea/nginx-devel/ubuntu trusty main
    - dist: trusty
    - file: /etc/apt/sources.list.d/nginx-devel.list
    - keyid: 136221EE520DDFAF0A905689B9316A7BC7917B12
    - keyserver: keyserver.ubuntu.com
    - require_in: install-nginx

install-nginx:
  pkg.latest:
    - fromrepo: trusty
    - pkgs:
      - nginx-full


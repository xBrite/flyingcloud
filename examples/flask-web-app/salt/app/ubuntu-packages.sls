ubuntu.packages:
  pkg.latest:
    - fromrepo: trusty
    - pkgs:
      - dnsutils

# nginx reverse proxy
/etc/nginx/sites-enabled/default:
  file.managed:
    - source: salt://nginx-default-site
    - makedirs: True

/etc/service/flask-example/run:
  file.managed:
    - source: salt://flask-example.sh
    - makedirs: True
    - mode: 0755

/etc/service/nginx/run:
  file.managed:
    - source: salt://nginx.sh
    - makedirs: True
    - mode: 0755



base:
  '*':
    {% if grains['os'] == 'Debian' or grains['os'] == 'Ubuntu' %}
    - nginx
    - ubuntu-packages
    {% endif %}
    - flask-example


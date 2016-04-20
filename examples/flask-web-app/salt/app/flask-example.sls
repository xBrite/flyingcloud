{% set venv = salt['environ.get']('VIRTUAL_ENV') %}
{% if not venv %}
    {% set venv = '/venv' %}
{% endif %}
app_venv:
  virtualenv.managed:
    - name: {{ venv }}

opencv_workaround:
  cmd.run:
    {% if grains['os'] == 'Ubuntu' %}
    - name: cp /usr/lib/python2.7/dist-packages/cv* {{ venv }}/lib/python2.7/site-packages/
    {% elif grains['os'] == 'MacOS' %}
    - name: cp /usr/local/lib/python2.7/site-packages/cv* {{ venv }}/lib/python2.7/site-packages/
    {% endif %}

app_requirements:
  pip.installed:
    - bin_env: {{ venv }}
    - requirements: /srv/salt/application/flask_example_app/requirements.txt

copy_application_files:
  cmd.run:
    - name: cp -r /srv/salt/application/flask_example_app {{ venv }}/lib/python2.7/site-packages



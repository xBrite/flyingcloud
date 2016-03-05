app_venv:
  virtualenv.managed:
    - name: /venv

app_requirements:
  pip.installed:
    - bin_env: /venv
    - requirements: salt://application/flask_example_app/requirements.txt

/venv/lib/python2.7/site-packages/flask_example_app:
  file.recurse:
    - source: salt://application/flask_example_app
    - user: root
    - group: root



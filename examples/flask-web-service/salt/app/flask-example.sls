app_venv:
  virtualenv.managed:
    - name: /venv

app_requirements:
  pip.installed:
    - bin_env: /venv
    - requirements: salt://application/app/requirements.txt

/venv/lib/python2.7/site-packages/app:
  file.recurse:
    - source: salt://application/app
    - user: root
    - group: root



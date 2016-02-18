app_venv:
  virtualenv.managed:
    - name: /venv

Cython:
  pip.installed:
    - name: 'Cython>=0.17'
    - bin_env: /venv
    - use_wheel: true

Pillow:
  pip.installed:
    - name: 'Pillow>=2.5.0'
    - bin_env: /venv
    - use_wheel: true

six:
  pip.installed:
    - name: 'six==1.7.3'
    - bin_env: /venv
    - use_wheel: true

numpy:
  pip.installed:
    - name: 'numpy==1.9.0'
    - bin_env: /venv
    - use_wheel: true

scipy:
  pip.installed:
    - name: 'scipy==0.14.0'
    - bin_env: /venv
    - use_wheel: true

scikit_image:
  pip.installed:
    - name: 'scikit-image==0.10.1'
    - bin_env: /venv
    - use_wheel: true

# "Install" OpenCV into the virtualenv (it can't be installed with pip)
opencv_workaround:
  cmd.run:
    - name: cp /usr/lib/python2.7/dist-packages/cv* /venv/lib/python2.7/site-packages/

python_tesseract:
  cmd.run:
    - name: /venv/bin/easy_install https://s3.amazonaws.com/cookbrite-public-storage/lectern/python_tesseract-0.9-py2.7-linux-x86_64.egg
    - unless: /venv/bin/python -c 'import tesseract'

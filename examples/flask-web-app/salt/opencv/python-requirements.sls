# "Install" OpenCV into the virtualenv (it can't be installed with pip)
opencv_workaround:
  cmd.run:
    - name: cp /usr/lib/python2.7/dist-packages/cv* /venv/lib/python2.7/site-packages/


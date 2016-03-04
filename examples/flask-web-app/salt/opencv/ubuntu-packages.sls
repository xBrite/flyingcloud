ubuntu.packages:
  pkg.latest:
    - fromrepo: trusty
    - pkgs:
      - libjpeg-dev
      - zlib1g-dev
      - python-opencv

# workaround for OpenCV on Linux trying to open nonexistent IEEE1394 device
/dev/raw1394:
  file.symlink:
    - target: /dev/null

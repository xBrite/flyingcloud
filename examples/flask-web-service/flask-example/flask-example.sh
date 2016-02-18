#!/bin/bash
exec /venv/bin/uwsgi -s /tmp/uwsgi.sock --chdir /venv/lib/python2.7/site-packages/app --module app --callable app --uid www-data --gid www-data

#!/usr/bin/env bash

set -o errexit
set -o nounset

rm -f './celerybeat.pid'

python manage.py migrate
celery -A agent beat -l INFO --pidfile=/code/celerybeat.pid
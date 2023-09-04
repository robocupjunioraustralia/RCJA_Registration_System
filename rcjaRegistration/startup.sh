#!/bin/sh

manage.py migrate --noinput
manage.py collectstatic --noinput
gunicorn --bind=0.0.0.0 --timeout 600 rcjaRegistration.wsgi

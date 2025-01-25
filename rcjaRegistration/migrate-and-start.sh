#!/bin/bash
echo "Start Database Migration"

manage.py migrate --noinput
manage.py collectstatic --noinput

echo "Lift off!"

gunicorn --bind 0.0.0.0:8000 --workers 3 rcjaRegistration.wsgi:application

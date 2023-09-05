#!/bin/bash
echo "Start Database Migration"

manage.py migrate --noinput
manage.py collectstatic --noinput

echo "Lift off!"

exec "$@"
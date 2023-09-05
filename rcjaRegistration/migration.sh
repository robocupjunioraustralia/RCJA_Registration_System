#!/bin/bash
echo "Migrate the Database at startup of project"

manage.py migrate --noinput
manage.py collectstatic --noinput

exec "$@"
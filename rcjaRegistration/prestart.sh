#! /usr/bin/env bash

if [ -z "$DYNO" ]; then
  manage.py herokuinit
fi

# Collect static
manage.py collectstatic --noinput

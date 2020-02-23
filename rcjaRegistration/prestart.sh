#! /usr/bin/env bash

if [ -n "$DYNO" ]; then
  manage.py herokuinit
fi

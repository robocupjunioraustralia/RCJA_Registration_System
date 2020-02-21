#! /usr/bin/env bash

manage.py migrate --noinput
manage.py collectstatic --noinput

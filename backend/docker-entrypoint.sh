#!/bin/bash

echo "Collect static files"
python manage.py collectstatic --noinput

echo "Run gunicorn server"
gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000
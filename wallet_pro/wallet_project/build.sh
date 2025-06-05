#!/usr/bin/env bash

echo "Running Django migrations..."

cd wallet_pro  # Only if manage.py is inside this folder

python manage.py makemigrations
python manage.py migrate

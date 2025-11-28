#!/bin/sh

until python manage.py migrate
do
    echo "Waiting for db to be ready..."
    sleep 2
done

until python manage.py createsuperuser
do
    echo "Waiting for superuser to be ready..."
    sleep 2
done


python manage.py runserver 0.0.0.0:8000
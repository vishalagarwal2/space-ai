#!/bin/sh


celery -A coreliaOS worker --pool=threads --concurrency=4 --loglevel=info --loglevel=info
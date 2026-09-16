#!/bin/sh
set -e
echo "1. Collecting static..."
python manage.py collectstatic --noinput

# The Magic Line: This takes the "command" from docker-compose and executes it here.
exec "$@"
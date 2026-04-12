#!/bin/bash
set -e

export PORT=${PORT:-5000}

exec gunicorn --bind 0.0.0.0:$PORT --workers 2 app.main:app